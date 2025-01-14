import logging
import random
import string
import zlib

from PIL.Image import DecompressionBombError
from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.template import Library
from django.utils.translation import ugettext as _

from astrobin.models import Image, ImageRevision
from astrobin_apps_images.services import ImageService
from astrobin_apps_iotd.services import IotdService

register = Library()
logger = logging.getLogger('apps')


# Returns the URL of an image, taking into account the fact that it might be
# a commercial gear image.
@register.simple_tag
def get_image_url(image, revision='final', size='regular'):
    return image.get_absolute_url(revision, size)


@register.filter
def gallery_thumbnail(image, revision_label):
    return image.thumbnail('gallery', revision_label)


@register.filter
def gallery_thumbnail_inverted(image, revision_label):
    return image.thumbnail('gallery_inverted', revision_label)


# Renders an linked image tag with a placeholder and async loading of the
# actual thumbnail.
def astrobin_image(context, image, alias, **kwargs):
    request = kwargs.get('request', context['request'])

    revision = kwargs.get('revision', 'final')
    url_size = kwargs.get('url_size', 'regular')
    url_revision = kwargs.get('url_revision', revision)
    link = kwargs.get('link', True)
    tooltip = kwargs.get('tooltip', True)
    nav_ctx = kwargs.get('nav_ctx', None)
    nav_ctx_extra = kwargs.get('nav_ctx_extra', None)
    classes = kwargs.get('classes', '')

    if nav_ctx is None:
        nav_ctx = request.GET.get('nc')
        if nav_ctx is not None:
            request.session['nav_ctx'] = nav_ctx
    if nav_ctx is None:
        nav_ctx = context.get('nav_ctx')
    if nav_ctx is None:
        nav_ctx = request.session.get('nav_ctx')
    if nav_ctx is None:
        nav_ctx = 'user'

    if nav_ctx_extra is None:
        nav_ctx_extra = request.GET.get('nce')
        if nav_ctx_extra is not None:
            request.session['nav_ctx_extra'] = nav_ctx_extra
    if nav_ctx_extra is None:
        nav_ctx_extra = context.get('nav_ctx_extra')
    if nav_ctx_extra is None:
        nav_ctx_extra = request.session.get('nav_ctx_extra')

    if 'nav_ctx_extra' in request.session and nav_ctx not in (
            # Contexts that support the extra argument
            'collection',
            'group',):
        del request.session['nav_ctx_extra']
        nav_ctx_extra = None

    response_dict = {
        'provide_size': True,
    }

    if alias == '':
        alias = 'gallery'

    if alias in ('gallery_inverted', 'regular_inverted', 'hd_inverted', 'real_inverted'):
        mod = 'inverted'
    else:
        mod = None

    size = settings.THUMBNAIL_ALIASES[''][alias]['size']

    if image is None or not isinstance(image, Image):
        return {
            'status': 'failure',
            'image': '',
            'alias': alias,
            'revision': revision,
            'size_x': size[0],
            'size_y': size[1],
            'caption_cache_key': 'astrobin_image_no_image',
            'nav_ctx': nav_ctx,
            'nav_ctx_extra': nav_ctx_extra,
            'classes': classes,
            'corrupted': False,
            'recovered': False,
            'is_revision': False,
        }

    # Old images might not have a size in the database, let's fix it.
    image_revision = image
    if revision not in [0, '0', 'final']:
        try:
            image_revision = image.revisions.get(label=revision)
        except ImageRevision.DoesNotExist:
            # Image revision was deleted
            pass

    w = image_revision.w
    h = image_revision.h

    if w == 0 or h == 0:
        try:
            from django.core.files.images import get_image_dimensions
            (w, h) = get_image_dimensions(image_revision.image_file.file)
            image_revision.w = w
            image_revision.h = h
            image_revision.save(keep_deleted=True)
        except (IOError, ValueError, DecompressionBombError) as e:
            w = size[0]
            h = size[1] if size[1] > 0 else w
            logger.warning("astrobin_image tag: unable to get image dimensions for revision %d: %s" % (
                image_revision.pk, str(e)))
            response_dict['status'] = 'error'
            response_dict['error_message'] = _("Data corruption. Please upload this image again. Sorry!")
        except (TypeError, zlib.error) as e:
            w = size[0]
            h = size[1] if size[1] > 0 else w
            logger.warning("astrobin_image tag: unable to get image dimensions for revision %d: %s" % (
                image_revision.pk, str(e)))

    if alias in (
            'regular', 'regular_inverted', 'regular_sharpened',
            'regular_large', 'regular_large_inverted', 'regular_large_sharpened',
            'hd', 'hd_inverted', 'hd_sharpened',
            'real', 'real_inverted'
    ):
        size = (size[0], int(size[0] / (w / float(h))))
        response_dict['provide_size'] = False

    placehold_size = [size[0], size[1]]
    for i in range(0, 2):
        if placehold_size[i] > 1920:
            placehold_size[i] = 1920

    if w < placehold_size[0]:
        placehold_size[0] = w
        placehold_size[1] = h

    # Determine whether this is an animated gif, and we should show it as such
    field = image.get_thumbnail_field(revision)
    if not field.name.startswith('images/'):
        field.name = 'images/' + field.name

    animated = field.name.lower().endswith('.gif') and \
               alias in (
                   'regular', 'regular_sharpened',
                   'regular_large', 'regular_large_sharpened',
                   'hd', 'hd_sharpened',
                   'real')

    url = get_image_url(image, url_revision, url_size)

    show_tooltip = tooltip and (alias in (
        'gallery', 'gallery_inverted',
        'thumb',
    ))

    ##########
    # BADGES #
    ##########

    badges = []

    if alias in (
            'thumb', 'gallery', 'gallery_inverted',
            'regular', 'regular_inverted', 'regular_sharpened',
            'regular_large', 'regular_large_inverted', 'regular_large_sharpened',
    ):

        if IotdService().is_iotd(image):
            badges.append('iotd')
        elif IotdService().is_top_pick(image):
            badges.append('top-pick')
        elif IotdService().is_top_pick_nomination(image):
            badges.append('top-pick-nomination')
        elif image.is_wip:
            badges.append('wip')

        # Temporarily disable this because it hogs the default celery queue.
        """
        cache_key = 'top100_ids'
        top100_ids = cache.get(cache_key)
        if top100_ids is None:
            from astrobin.tasks import update_top100_ids
            update_top100_ids.delay()
        elif image.pk in top100_ids:
            badges.append('top100')
        """

    cache_key = image.thumbnail_cache_key(field, alias)
    if animated:
        cache_key += '_animated'
    thumb_url = cache.get(cache_key)

    # Force HTTPS
    if thumb_url and request.is_secure():
        thumb_url = thumb_url.replace('http://', 'https://', 1)

    # If we're testing, we want to bypass the placeholder thing and force-get
    # the thumb url.
    if thumb_url is None and settings.TESTING:
        thumb = image.thumbnail_raw(alias, revision)
        if thumb:
            thumb_url = thumb.url

    get_thumb_url = None
    if thumb_url is None:
        get_thumb_kwargs = {
            'id': image.hash if image.hash else image.id,
            'alias': alias,
        }

        if revision is None or revision != 'final':
            get_thumb_kwargs['r'] = revision

        get_thumb_url = reverse('image_thumb', kwargs=get_thumb_kwargs)
        if animated:
            get_thumb_url += '?animated'

    get_regular_large_thumb_url, regular_large_thumb_url = ImageService(image).get_enhanced_thumb_url(
        field, alias, revision, animated, request.is_secure(), 'regular_large')

    get_enhanced_thumb_url, enhanced_thumb_url = ImageService(image).get_enhanced_thumb_url(
        field, alias, revision, animated, request.is_secure(), 'hd')


    return dict(response_dict.items() + {
        'status': 'success',
        'image': image,
        'alias': alias,
        'mod': mod,
        'revision': revision,
        'size_x': size[0],
        'size_y': size[1],
        'placehold_size': "%sx%s" % (placehold_size[0], placehold_size[1]),
        'real': alias in ('real', 'real_inverted'),
        'url': url,
        'show_tooltip': show_tooltip,
        'request': request,
        'caption_cache_key': "%d_%s_%s_%s" % (
            image.id, revision, alias, request.LANGUAGE_CODE if hasattr(request, "LANGUAGE_CODE") else "en"),
        'badges': badges,
        'animated': animated,
        'get_thumb_url': get_thumb_url,
        'thumb_url': thumb_url,
        'link': link,
        'nav_ctx': nav_ctx,
        'nav_ctx_extra': nav_ctx_extra,
        'classes': classes,
        'enhanced_thumb_url': enhanced_thumb_url,
        'get_enhanced_thumb_url': get_enhanced_thumb_url,
        'regular_large_thumb_url': regular_large_thumb_url,
        'get_regular_large_thumb_url': get_regular_large_thumb_url,
        'corrupted': image_revision.corrupted,
        'recovered': image_revision.recovered is not None,
        'is_revision': hasattr(image_revision, 'label'),
        'revision_id': image_revision.pk,
        'w': w,
        'h': h,
    }.items())


register.inclusion_tag(
    'astrobin_apps_images/snippets/image.html',
    takes_context=True)(astrobin_image)


@register.simple_tag(takes_context=True)
def random_id(context, size=8, chars=string.ascii_uppercase + string.digits):
    id = ''.join(random.choice(chars) for x in range(size))
    context['randomid'] = id
    return ''
