import Foundation

// Shapes of what cptutor/api.py returns.  Nearly everything is Optional: the API is
// loosely shaped (a step view differs by kind, a case shows its input only when it
// failed), and one unexpected null must not blank a whole screen.

struct Block: Decodable, Hashable {
    let type: String
    var text: String?
    var lang: String?
    var rows: [[String]]?
    var n: Int?
}

typealias Blocks = [Block]

struct BalloonRef: Decodable, Hashable {
    let ref: String
    let solved: Bool
    let color: String
}

struct LessonRow: Decodable, Identifiable, Hashable {
    let id: String
    let title: String
    var track: String?
    var summary: String?
    var status: String?
    var parts: Int?
    var questions: Int?
    var answered: Int?
    var problems: Int?
    var solved: Int?
    var cards: Int?
    var due: Int?
    var minutes: Int?
    var prereqs: [String]?
    var missing: [String]?
    var balloons: [BalloonRef]?
    var state: String?          // today's "upcoming": started | open | ahead
}

struct Track: Decodable, Identifiable {
    var id: String { track }
    let track: String
    let name: String
    var blurb: String?
    let lessons: [LessonRow]
}

struct LessonsPayload: Decodable { let tracks: [Track] }

struct ProblemRow: Decodable, Identifiable, Hashable {
    var id: String { ref }
    let ref: String
    var lesson: String?
    var lessonTitle: String?
    let title: String
    var difficulty: String?
    var source: String?
    var color: String?
    var solved: Bool?
    var submits: Int?
    var gaveUp: Bool?
    var due: Bool?
    var nextReview: String?
    var statement: String?      // clipped plain text, in a lesson view
}

// ----------------------------------------------------------------------- today
struct PlanRow: Decodable, Identifiable {
    var id: String { key }
    let key: String
    let title: String
    let state: String
    let detail: String
    let minutes: Int
    let route: String
}

struct RecentVerdict: Decodable, Identifiable {
    var id: String { ref + ts }
    let ref: String
    let title: String
    let verdict: String
    let ts: String
    let color: String
}

struct Retention: Decodable, Identifiable {
    var id: String { lesson }
    let lesson: String
    let label: String
    let reviews: Int
    let pct: Int
}

struct Today: Decodable {
    let today: String
    let day: Int
    let streak: Int
    let best: Int
    let minutes: Int
    let target: Int
    let due: Int
    let learned: Int
    let lessons: Int
    let solved: Int
    let problems: Int
    let plan: [PlanRow]
    let upcoming: [LessonRow]
    let forecast: [Int]
    let recent: [RecentVerdict]
    let retention: [Retention]
    var warnings: [String]?
}

// ---------------------------------------------------------------------- lesson
struct PartView: Decodable, Identifiable {
    var id: Int { first }
    let title: String
    let first: Int
    let gates: Int
    let done: Int
    let open: Bool
}

struct Picked: Decodable, Hashable {
    let i: Int
    let correct: Bool
    var why: Blocks?
}

struct Response: Decodable, Hashable {
    let text: String
    let correct: Bool
    var feedback: Blocks?
}

struct StepView: Decodable, Identifiable, Hashable {
    var id: Int { k }
    let k: Int
    let part: Int
    let kind: String
    var blocks: Blocks?
    var done: Bool?
    // try
    var ref: String?
    var title: String?
    var difficulty: String?
    var note: Blocks?
    var solved: Bool?
    var skipped: Bool?
    var submits: Int?
    // questions
    var q: Blocks?
    var tries: Int?
    var options: [String]?
    var picked: [Picked]?
    var unit: String?
    var placeholder: String?
    var hasHint: Bool?
    var hint: Blocks?
    var responses: [Response]?
    var correct: Bool?
    var revealed: Bool?
    var mine: String?
    var answer: Blocks?
    var selfRating: String?
    var right: [Int]?
    var explain: Blocks?

    enum CodingKeys: String, CodingKey {
        case k, part, kind, blocks, done, ref, title, difficulty, note, solved, skipped, submits
        case q, tries, options, picked, unit, placeholder, hasHint, hint, responses, correct, revealed
        case mine, answer, right, explain
        case selfRating = "self"
    }

    var isDone: Bool { done ?? false }
}

struct CardView: Decodable, Identifiable, Hashable {
    var id: String { item }
    let item: String
    let lesson: String
    let q: Blocks
    let a: Blocks
    let seen: Bool
    var due: String?
    var isDue: Bool?
    var intervals: [Int]?
}

struct LessonLink: Decodable, Identifiable, Hashable {
    let id: String
    let title: String
    var done: Bool?
}

struct LessonPayload: Decodable {
    let lesson: LessonRow
    var parts: [PartView]
    var steps: [StepView]
    var reached: Int
    let total: Int
    var finished: Bool
    var problems: [ProblemRow]
    var cards: [CardView]
    var prereqs: [LessonLink]
    var unlocks: [LessonLink]
    var next: LessonLink?
    var tags: [String]?
}

struct AnswerResult: Decodable {
    var correct: Bool?
    var invalid: Bool?
    var feedback: Blocks?
    var `repeat`: Bool?
}

struct Progress: Decodable { let done: Int; let total: Int }

struct Advance: Decodable {
    let step: StepView
    var unfolded: [StepView]?
    let reached: Int
    var finished: Bool?
    var learned: Bool?
    var progress: Progress?
    var result: AnswerResult?
}

struct StepOnly: Decodable { let step: StepView }

// --------------------------------------------------------------------- problem
struct Sample: Decodable, Hashable {
    let input: String
    var output: String?
    var note: Blocks?
}

struct Submission: Decodable, Identifiable, Hashable {
    var id: String { ts + verdict }
    var ref: String?
    let ts: String
    let verdict: String
    var failed: String?
    var ms: Int?
    var passed: Int?
    var total: Int?
}

struct Sibling: Decodable, Identifiable, Hashable {
    var id: String { ref }
    let ref: String
    let title: String
    let color: String
    let solved: Bool
}

struct SRS: Decodable {
    let scheduled: Bool
    var due: String?
    var isDue: Bool?
}

struct ProblemPayload: Decodable {
    let ref: String
    var lesson: String?
    var lessonTitle: String?
    let title: String
    var difficulty: String?
    var source: String?
    var color: String?
    var solved: Bool?
    var submits: Int?
    var gaveUp: Bool?
    var due: Bool?
    let statement: Blocks
    let input: Blocks
    let output: Blocks
    let samples: [Sample]
    var timeLimit: Double?
    var complexity: String?
    var hintsTotal: Int?
    var hints: [Blocks]?
    var editorial: Blocks?
    var solution: String?
    let code: String
    var starter: String?
    var path: String?
    var submissions: [Submission]?
    var siblings: [Sibling]?
    var wrong: Int?
    var graded: Bool?
    var srs: SRS?
    // contest view
    var letter: String?
    var contest: ContestView?
    var row: ContestRow?
    var subs: [ContestSub]?
}

struct HintsPayload: Decodable { let hints: [Blocks]; let total: Int }
struct EditorialPayload: Decodable { let editorial: Blocks; let solution: String; var learned: Bool? }
struct CodePayload: Decodable { let code: String }
struct GradePayload: Decodable { let quality: Int; let interval: Int; let due: String }

struct JudgeCase: Decodable, Identifiable, Hashable {
    var id: String { name }
    let name: String
    var kind: String?
    var gen: String?
    var large: Bool?
    var ms: Int?
    var kb: Int?
    var note: String?
    let verdict: String
    var message: String?
    var input: String?
    var inputSize: Int?
    var expected: String?
    var got: String?
    var stderr: String?
    var hidden: Bool?

    // `note` is a plain string from judge.py but blocks in a sample: accept either.
    enum CodingKeys: String, CodingKey {
        case name, kind, gen, large, ms, kb, note, verdict, message, input, inputSize, expected, got, stderr, hidden
    }

    init(from d: Decoder) throws {
        let c = try d.container(keyedBy: CodingKeys.self)
        name = try c.decode(String.self, forKey: .name)
        kind = try c.decodeIfPresent(String.self, forKey: .kind)
        gen = try c.decodeIfPresent(String.self, forKey: .gen)
        large = try c.decodeIfPresent(Bool.self, forKey: .large)
        ms = try c.decodeIfPresent(Int.self, forKey: .ms)
        kb = try c.decodeIfPresent(Int.self, forKey: .kb)
        if let s = try? c.decodeIfPresent(String.self, forKey: .note) {
            note = s
        } else if let b = try? c.decodeIfPresent(Blocks.self, forKey: .note) {
            note = b.compactMap { $0.text }.joined(separator: " ")
        } else {
            note = nil
        }
        verdict = try c.decode(String.self, forKey: .verdict)
        message = try c.decodeIfPresent(String.self, forKey: .message)
        input = try c.decodeIfPresent(String.self, forKey: .input)
        inputSize = try c.decodeIfPresent(Int.self, forKey: .inputSize)
        expected = try c.decodeIfPresent(String.self, forKey: .expected)
        got = try c.decodeIfPresent(String.self, forKey: .got)
        stderr = try c.decodeIfPresent(String.self, forKey: .stderr)
        hidden = try c.decodeIfPresent(Bool.self, forKey: .hidden)
    }
}

struct JudgeResult: Decodable {
    let verdict: String
    var failed: String?
    var passed: Int?
    var total: Int?
    var ran: Int?
    var cases: [JudgeCase]?
    var maxMs: Int?
    var maxKb: Int?
    var timeLimit: Double?
    var compile: String?
    var warnings: String?
}

struct RunPayload: Decodable {
    let result: JudgeResult
    var firstAc: Bool?
    var learned: Bool?
    var state: ProblemRow?
    var srs: SRS?
    var reviewing: Bool?
    var contest: ContestView?
}

struct CustomResult: Decodable {
    let verdict: String
    var compile: String?
    var stdout: String?
    var stderr: String?
    var ms: Int?
    var kb: Int?
    var message: String?
    var warnings: String?
    var reference: String?
    var referenceError: String?
    var matches: Bool?
}

// -------------------------------------------------------------------- problems
struct ProblemGroupLesson: Decodable, Identifiable {
    let id: String
    let title: String
    var status: String?
    let problems: [ProblemRow]
}

struct ProblemGroup: Decodable, Identifiable {
    var id: String { track }
    let track: String
    let name: String
    let lessons: [ProblemGroupLesson]
}

struct ProblemsPayload: Decodable { let groups: [ProblemGroup] }

// ---------------------------------------------------------------------- review
struct DueItem: Decodable, Identifiable {
    var id: String { item }
    let kind: String
    let item: String
    let lesson: String
    var lessonTitle: String?
    var card: CardView?
    var problem: ProblemRow?
}

struct DuePayload: Decodable { let queue: [DueItem] }

// ----------------------------------------------------------------------- stats
struct TrackStats: Decodable, Identifiable {
    var id: String { track }
    let track: String
    let name: String
    let learned: Int
    let total: Int
    let solved: Int
    let problems: Int
}

struct Hardest: Decodable, Identifiable {
    var id: String { item }
    let item: String
    let lesson: String
    let kind: String
    let label: String
    let ease: Double
    var ref: String?
}

struct Stats: Decodable {
    let tracks: [TrackStats]
    let verdicts: [String: Int]
    let submissions: Int
    let solved: Int
    let problems: Int
    let firstTryPct: Int
    let questions: Int
    let cardsSeen: Int
    let cardsTotal: Int
    let reviews: Int
    let remembered: Int
    let streak: Int
    let best: Int
    let forecast: [Int]
    let hardest: [Hardest]
    let retention: [Retention]
    let activity: [Int]
    let activityWeeks: Int
    let hours: Double
    let lessonsLearned: Int
    let lessonsTotal: Int
}

// --------------------------------------------------------------------- contest
struct ContestRow: Decodable, Identifiable, Hashable {
    var id: String { letter }
    let letter: String
    let ref: String
    let title: String
    let color: String
    let solved: Bool
    var minute: Int?
    var wrong: Int?
    var tries: Int?
    var penalty: Int?
    var last: String?
    var lesson: String?
    var lessonTitle: String?
    var difficulty: String?
    var source: String?
}

struct ContestSub: Decodable, Identifiable, Hashable {
    var id: String { ts }
    let ref: String
    let minute: Int
    let verdict: String
    let ts: String
}

struct ContestView: Decodable {
    let id: Int
    let started: String
    let minutes: Int
    let elapsed: Int
    let remaining: Int
    let finished: Bool
    var ended: String?
    let solved: Int
    let penalty: Int
    let rows: [ContestRow]
    var pool: String?
}

struct PastContest: Decodable, Identifiable {
    let id: Int
    let started: String
    let minutes: Int
    let solved: Int
    let penalty: Int
    let problems: Int
}

struct ContestPayload: Decodable {
    var active: ContestView?
    var last: ContestView?
    let past: [PastContest]
    var studied: Int?
}

struct ContestStarted: Decodable { let active: ContestView }
struct ContestEnded: Decodable { let last: ContestView }

// -------------------------------------------------------------------- notebook
struct NotebookProblem: Decodable, Identifiable {
    var id: String { ref }
    let ref: String
    let title: String
    let color: String
    var complexity: String?
    var source: String?
    var mine: String?
    let reference: String
}

struct NotebookLesson: Decodable, Identifiable {
    let id: String
    let title: String
    var track: String?
    let problems: [NotebookProblem]
}

struct NotebookPayload: Decodable { let lessons: [NotebookLesson] }

// ------------------------------------------------------------------------- env
struct CompilerInfo: Decodable {
    let ok: Bool
    var version: String?
    var path: String?
    var gcc: Bool?
    var flags: String?
    var error: String?
}

struct Env: Decodable {
    let compiler: CompilerInfo
    var progress: String?
    var workspace: String?
    var loadErrors: [String: String]?
}

struct Ping: Decodable { let lessons: Int }
