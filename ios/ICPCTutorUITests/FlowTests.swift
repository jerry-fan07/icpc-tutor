import XCTest

/// End-to-end against a tutor server on 127.0.0.1:8123 (start one with CPTUTOR_DATA and
/// CPTUTOR_WORKSPACE pointed at a scratch copy: these flows change progress).
final class FlowTests: XCTestCase {
    func launch(_ route: String, _ extra: [String] = []) -> XCUIApplication {
        let app = XCUIApplication()
        app.launchArguments = ["-serverURL", "http://127.0.0.1:8123", "-route", route] + extra
        app.launch()
        return app
    }

    func testRevealAdvancesDialogue() {
        // whichever question cpp05 is waiting on, "show me" is always there
        let app = launch("#/lesson/cpp05")
        let show = app.buttons.matching(NSPredicate(format: "label ENDSWITH 'show me'")).firstMatch
        XCTAssertTrue(show.waitForExistence(timeout: 15))
        show.tap()
        let shown = app.staticTexts.matching(NSPredicate(format: "label == 'shown' OR label == 'the tutor'")).firstMatch
        XCTAssertTrue(shown.waitForExistence(timeout: 15))
        // the next stretch unfolded: one more question box, or the end of the dialogue
        let next = app.staticTexts.matching(NSPredicate(format: "label BEGINSWITH 'Q'")).count
        XCTAssertGreaterThan(next, 0)
    }

    func testMCQPick() {
        // algo07 opens with a multiple-choice question; pick option A whatever it is
        let app = launch("#/lesson/algo07")
        let opt = app.buttons["opt-0"].firstMatch
        XCTAssertTrue(opt.waitForExistence(timeout: 15))
        opt.tap()
        // right: the feedback line appears; wrong: the option is struck out and disabled
        let fb = app.staticTexts.matching(NSPredicate(format: "label BEGINSWITH '✓'")).firstMatch
        let disabled = NSPredicate(format: "isEnabled == false")
        let tapped = app.buttons.matching(identifier: "opt-0").matching(disabled).firstMatch
        XCTAssertTrue(fb.waitForExistence(timeout: 15) || tapped.waitForExistence(timeout: 15))
    }

    func testTypedWrongAnswerStays() {
        // cpp03 opens with a short-answer question; a wrong answer is listed, nothing unfolds
        let app = launch("#/lesson/cpp03")
        let field = app.textFields.firstMatch
        XCTAssertTrue(field.waitForExistence(timeout: 15))
        field.tap()
        field.typeText("zzz-not-an-answer")
        app.buttons["check"].firstMatch.tap()
        XCTAssertTrue(app.staticTexts["✗"].firstMatch.waitForExistence(timeout: 15))
        XCTAssertTrue(app.staticTexts["zzz-not-an-answer"].firstMatch.exists)
    }

    func snap(_ name: String) {
        guard let dir = ProcessInfo.processInfo.environment["SHOT_DIR"] else { return }
        try? XCUIScreen.main.screenshot().pngRepresentation.write(to: URL(fileURLWithPath: dir).appendingPathComponent(name + ".png"))
    }

    func testRunSamplesJudges() {
        let app = launch("#/problem/cpp02.multiples_in_range", ["-solve"])
        let run = app.buttons["run samples"]
        XCTAssertTrue(run.waitForExistence(timeout: 15))
        run.tap()
        let verdict = app.staticTexts.matching(NSPredicate(
            format: "label BEGINSWITH 'Wrong Answer' OR label BEGINSWITH 'Samples pass' OR label BEGINSWITH 'Compilation'")).firstMatch
        XCTAssertTrue(verdict.waitForExistence(timeout: 180))
        snap("t_judge")
    }

    func testPlaygroundRuns() {
        let app = launch("#/playground")
        let run = app.buttons["run"]
        XCTAssertTrue(run.waitForExistence(timeout: 15))
        run.tap()
        XCTAssertTrue(app.staticTexts["ran"].waitForExistence(timeout: 180))
        XCTAssertTrue(app.staticTexts.matching(NSPredicate(format: "label BEGINSWITH '1 1 3 4 5'")).firstMatch.waitForExistence(timeout: 5))
        app.swipeUp()
        snap("t_playground")
    }

    func testCardReviewFlow() {
        let app = launch("#/review")
        XCTAssertTrue(app.staticTexts["review"].firstMatch.waitForExistence(timeout: 15))
    }
}
