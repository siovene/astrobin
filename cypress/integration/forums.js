describe("Forums", () => {
    before(() => {
        cy.login({next: "/forum/"});
    });

    beforeEach(() => {
        Cypress.Cookies.preserveOnce("sessionid", "csrftoken", "astrobin_lang", "cookielaw_accepted");
    });

    it("should have default forum", () => {
       cy.get(".forum-name").contains("AstroBin Meta Forums").should("exist");
       cy.get(".forum-name a").contains("Announcements").should("exist");
    });

    it("should post", () => {
        cy.visit("/forum/c/astrobin/announcements/");
        cy.get("a").contains("New topic").click();
        cy.url().should("contain", "/topic/add/");

        cy.get(".post-form input[name='name']").type("Test topic");
        cy.get(".post-form textarea[name='body'] + .wysibb-text-editor").type("Hello, this is a test topic.");
        cy.get(".post-form input[type='submit']").click();

        cy.url().should("contain", "/forum/c/astrobin/announcements/test-topic");
        cy.get(".topic h1").contains("Test topic").should("exist");
        cy.get(".post-content").contains("Hello, this is a test topic.").should("exist");
    });

    it("should edit", () => {
        cy.get(".post-related a").contains("Edit").click();
        cy.url().should("match", /\/forum\/post\/\d+\/edit\//);

        cy.get(".post-form input[name='name']").clear().type("Edited test topic");
        cy.get(".post-form textarea[name='body'] + .wysibb-text-editor")
            .clear()
            .type("Hello, this is an edited test topic.");
        cy.get(".post-form input[type='submit']").click();

        cy.url().should("contain", "/forum/c/astrobin/announcements/test-topic");
        cy.get(".topic h1").contains("Edited test topic").should("exist");
        cy.get(".post-content").contains("Hello, this is an edited test topic.").should("exist");
    });

    it("should reply", () => {
        cy.get(".post-form textarea[name='body'] + .wysibb-text-editor").type("This is a reply.");
        cy.get(".post-form input[type='submit']").click();

        cy.url().should("contain", "/forum/c/astrobin/announcements/test-topic");
        cy.get(".post-content").contains("This is a reply.").should("exist");
    });

    it("should quote", () => {
        cy.get(".post-related").last().contains("quote").click();
        cy
            .get(".post-form textarea[name='body'] + .wysibb-text-editor")
            .text()
            .should("contain", "[quote=\"astrobin_dev\"]This is a reply.[/quote]");
    });
});