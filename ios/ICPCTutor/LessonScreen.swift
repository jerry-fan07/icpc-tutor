import SwiftUI

let kindLabel: [String: String] = ["mcq": "choose", "numeric": "estimate", "short": "answer",
                                  "reflect": "think it through", "try": "now solve it"]

/// The dialogue.  Everything up to the next question is on the page; answering unfolds
/// the next stretch, exactly as web/app.js does it (`applyAdvance`).
@Observable
final class LessonModel {
    let id: String
    var d: LessonPayload? = nil
    var steps: [StepView] = []
    var reached = 0
    var error: String? = nil
    var scrollTo: Int? = nil

    init(id: String) { self.id = id }

    @MainActor
    func load() async {
        do {
            let p: LessonPayload = try await API.shared.get("lesson", ["id": id])
            d = p
            steps = p.steps
            reached = p.reached
            error = nil
            if p.reached > 0 { scrollTo = min(p.reached, p.total - 1) }
        } catch {
            if d == nil { self.error = error.localizedDescription }
        }
    }

    func replace(_ v: StepView) {
        if let i = steps.firstIndex(where: { $0.k == v.k }) { steps[i] = v } else { steps.append(v) }
        steps.sort { $0.k < $1.k }
    }

    @MainActor
    func apply(_ r: Advance, toast: Toast) async {
        replace(r.step)
        for v in r.unfolded ?? [] { replace(v) }
        let grew = r.reached != reached
        reached = r.reached
        if r.learned ?? false { toast.show("Lesson learned ✓") }
        if grew {
            // refresh the part counts (and, at the end, cards and problems) from the lesson view
            if let p: LessonPayload = try? await API.shared.get("lesson", ["id": id]) {
                d?.parts = p.parts
                d?.reached = p.reached
                d?.finished = p.finished
                d?.problems = p.problems
                d?.cards = p.cards
            }
        }
    }

    /// Q numbers: every question step in order, Try steps excluded.
    var qNumber: [Int: Int] {
        var n = 0, out: [Int: Int] = [:]
        for s in steps where s.kind != "say" && s.kind != "try" {
            n += 1; out[s.k] = n
        }
        return out
    }

    var total: Int { d?.total ?? 0 }
    var finished: Bool { reached >= total && total > 0 }
}

struct LessonScreen: View {
    let id: String
    @State private var m: LessonModel
    @Environment(Toast.self) private var toast
    @Environment(Armed.self) private var armed

    init(id: String) {
        self.id = id
        _m = State(initialValue: LessonModel(id: id))
    }

    var body: some View {
        Group {
            if let d = m.d {
                content(d)
            } else if let e = m.error {
                ErrorView(message: e) { await m.load() }
            } else {
                ProgressView().tint(Theme.muted).frame(maxWidth: .infinity, maxHeight: .infinity).background(Theme.paper)
            }
        }
        .task { await m.load() }
        .heartbeat()
        .navigationTitle(id)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            if let d = m.d {
                ToolbarItem(placement: .topBarTrailing) {
                    Menu {
                        ForEach(Array(d.parts.enumerated()), id: \.offset) { i, p in
                            Button {
                                m.scrollTo = p.first
                            } label: {
                                Label("\(i + 1). \(p.title)  \(p.done)/\(p.gates)", systemImage: p.gates > 0 && p.done >= p.gates ? "checkmark" : p.open ? "circle" : "lock")
                            }
                            .disabled(!p.open)
                        }
                    } label: {
                        Image(systemName: "list.bullet")
                    }
                }
            }
        }
    }

    private func content(_ d: LessonPayload) -> some View {
        ScrollViewReader { proxy in
            ScrollView {
                VStack(alignment: .leading, spacing: 0) {
                    let L = d.lesson
                    TitleLine(title: L.title, note: "\(L.id) · \(plural(L.parts ?? 0, "part")) · \(plural(L.questions ?? 0, "question")) · \(plural(L.problems ?? 0, "problem"))")
                    if let s = L.summary {
                        Text(s).font(Theme.sans(13)).foregroundStyle(Theme.muted).padding(.top, 6)
                    }
                    let nums = m.qNumber
                    ForEach(m.steps) { v in
                        if let pi = d.parts.firstIndex(where: { $0.first == v.k }) {
                            PartTitle(n: pi + 1, title: d.parts[pi].title)
                                .id("part-\(v.k)")
                        }
                        StepRow(m: m, v: v, qn: nums[v.k], problems: d.problems)
                            .id("step-\(v.k)")
                    }
                    if m.finished { tail(d) }
                    sidebar(d)
                }
                .padding(.horizontal, 18)
                .padding(.top, 8)
                .padding(.bottom, 60)
                .frame(maxWidth: 720)
                .frame(maxWidth: .infinity)
            }
            .background(Theme.paper)
            .scrollDismissesKeyboard(.interactively)
            .refreshable { await m.load() }
            .onAppear { jump(proxy, d) }
            .onChange(of: m.scrollTo) { _, _ in jump(proxy, d) }
        }
    }

    private func jump(_ proxy: ScrollViewProxy, _ d: LessonPayload) {
        guard let k = m.scrollTo else { return }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
            withAnimation { proxy.scrollTo(d.parts.contains { $0.first == k } ? "part-\(k)" : "step-\(k)", anchor: .top) }
            m.scrollTo = nil
        }
    }

    @ViewBuilder
    private func tail(_ d: LessonPayload) -> some View {
        let unsolved = d.problems.filter { !($0.solved ?? false) && !($0.gaveUp ?? false) }
        VStack(alignment: .leading, spacing: 8) {
            Text("End of the dialogue").font(Theme.sans(17, .medium)).foregroundStyle(Theme.ink)
            Text(unsolved.isEmpty
                 ? "Every problem here is solved or read. Rate the cards below; they come back in review."
                 : "Still open: " + unsolved.map { $0.title }.joined(separator: ", ") + ". The lesson counts as learned when each is solved (or its editorial read).")
                .font(Theme.sans(13)).foregroundStyle(Theme.muted)
            if let n = d.next {
                NavigationLink(value: Route.lesson(n.id)) { Text("next: \(n.id) \(n.title) →") }.buttonStyle(Outline())
            }
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .overlay(RoundedRectangle(cornerRadius: 9).stroke(Theme.hairline))
        .padding(.top, 40)
        if !d.cards.isEmpty {
            SectionHeading(title: "cards to remember", value: "\(d.cards.filter { $0.seen }.count) of \(d.cards.count) scheduled")
            ForEach(d.cards) { CardBlock(card: $0) }
        }
    }

    @ViewBuilder
    private func sidebar(_ d: LessonPayload) -> some View {
        SectionHeading(title: "problems", value: "\(d.problems.filter { $0.solved ?? false }.count)/\(d.problems.count)")
        VStack(spacing: 0) {
            ForEach(d.problems) { p in
                RowLink(route: .problem(p.ref)) {
                    Balloon(color: p.color ?? "#888888", solved: p.solved ?? false, size: 10)
                    Text(p.title).font(Theme.sans(14)).foregroundStyle(Theme.ink).lineLimit(1)
                    Spacer()
                    Chip(text: (p.solved ?? false) ? "✓" : (p.difficulty ?? ""))
                }
            }
        }
        .padding(.horizontal, -10)
        if !d.prereqs.isEmpty {
            SectionHeading(title: "builds on", rule: false)
            ForEach(d.prereqs) { p in
                NavigationLink(value: Route.lesson(p.id)) {
                    Text("\(p.id) \(p.title)" + ((p.done ?? false) ? " ✓" : "")).font(Theme.sans(13))
                        .foregroundStyle((p.done ?? false) ? Theme.pass : Theme.muted)
                }
                .padding(.vertical, 2)
            }
        }
        if !d.unlocks.isEmpty {
            SectionHeading(title: "opens up", rule: false)
            ForEach(d.unlocks) { u in
                NavigationLink(value: Route.lesson(u.id)) {
                    Text("\(u.id) \(u.title)").font(Theme.sans(13)).foregroundStyle(Theme.muted)
                }
                .padding(.vertical, 2)
            }
        }
        Button("restart this dialogue") {
            guard armed.twice("lesson", toast, "Tap again to clear your answers in this lesson (solved problems stay solved).") else { return }
            Task {
                try? await API.shared.post("lesson_reset", ["id": id])
                await m.load()
            }
        }
        .buttonStyle(Bare())
        .padding(.top, 28)
    }
}

struct PartTitle: View {
    let n: Int
    let title: String
    var body: some View {
        HStack(alignment: .firstTextBaseline, spacing: 10) {
            Text(String(format: "%02d", n)).font(Theme.mono(11.5)).foregroundStyle(Theme.accent)
            Text(inline(title, .sans(19, weight: .medium)))
        }
        .padding(.top, n == 1 ? 18 : 40)
        .padding(.bottom, 10)
    }
}

// MARK: - one step

struct StepRow: View {
    let m: LessonModel
    let v: StepView
    let qn: Int?
    let problems: [ProblemRow]

    var body: some View {
        switch v.kind {
        case "say":
            Prose(blocks: v.blocks ?? [], book: true).padding(.vertical, 12)
        case "try":
            TryStep(m: m, v: v, color: problems.first { $0.ref == v.ref }?.color ?? "#888888")
        default:
            QuestionStep(m: m, v: v, qn: qn ?? 0)
        }
    }
}

struct QuestionStep: View {
    let m: LessonModel
    let v: StepView
    let qn: Int
    @Environment(Toast.self) private var toast
    @State private var busy = false

    var body: some View {
        let done = v.isDone
        VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .firstTextBaseline, spacing: 8) {
                Text("Q\(qn)").font(Theme.mono(11.5)).foregroundStyle(done ? Theme.faint : Theme.accent)
                Text(kindLabel[v.kind] ?? v.kind).font(Theme.sans(12)).foregroundStyle(Theme.muted)
                Spacer()
                if !done && (v.hasHint ?? false) && v.hint == nil {
                    Button("hint") {
                        Task {
                            if let r: StepOnly = try? await API.shared.post("hint_step", ["lesson": m.id, "k": v.k]) { m.replace(r.step) }
                        }
                    }.buttonStyle(Bare())
                }
                if !done && v.kind != "reflect" {
                    Button((v.tries ?? 0) > 0 ? "show me" : "skip · show me") {
                        Task { await act { try await API.shared.post("reveal", ["lesson": m.id, "k": v.k]) } }
                    }.buttonStyle(Bare())
                }
            }
            Prose(blocks: v.q ?? [], book: true)

            switch v.kind {
            case "mcq": MCQBody(m: m, v: v, busy: $busy, act: act)
            case "reflect": ReflectBody(m: m, v: v, act: act)
            default: TypedBody(m: m, v: v, act: act)
            }

            if let h = v.hint, !done {
                VStack(alignment: .leading, spacing: 4) {
                    Text("hint").font(Theme.sans(11.5)).foregroundStyle(Theme.faint)
                    Prose(blocks: h, book: true, color: Theme.muted, size: 15)
                }
                .padding(.top, 4)
            }
            if done && v.kind != "reflect" {
                let n = v.tries ?? 0
                let revealed = v.revealed ?? false
                let answer = v.answer ?? []
                let explain = v.explain ?? []
                if revealed || !answer.isEmpty || !explain.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        Rectangle().fill(Theme.hairline).frame(height: 1)
                        Text(revealed ? "shown" : n <= 1 ? "✓ first try" : "✓ after \(n) tries")
                            .font(Theme.sans(12.5)).foregroundStyle(revealed ? Theme.faint : Theme.pass)
                        if !answer.isEmpty { Prose(blocks: answer, book: true, size: 15.5) }
                        if !explain.isEmpty { Prose(blocks: explain, book: true, size: 15.5) }
                    }
                    .padding(.top, 6)
                }
            }
        }
        .padding(.horizontal, 16).padding(.vertical, 14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(done ? .clear : Theme.raised)
        .overlay(alignment: .leading) {
            Rectangle().fill(done ? Theme.hairline : Theme.accent).frame(width: 3)
        }
        .clipShape(RoundedRectangle(cornerRadius: 9))
        .padding(.vertical, 12)
    }

    /// Run an op that advances the dialogue.
    func act(_ call: @escaping () async throws -> Advance) async {
        busy = true
        defer { busy = false }
        do {
            let r = try await call()
            await m.apply(r, toast: toast)
        } catch {
            toast.show(error.localizedDescription)
        }
    }
}

struct MCQBody: View {
    let m: LessonModel
    let v: StepView
    @Binding var busy: Bool
    let act: (@escaping () async throws -> Advance) async -> Void

    var body: some View {
        let picked = Dictionary(uniqueKeysWithValues: (v.picked ?? []).map { ($0.i, $0) })
        let right = Set(v.right ?? [])
        let done = v.isDone
        VStack(alignment: .leading, spacing: 7) {
            ForEach(Array((v.options ?? []).enumerated()), id: \.offset) { i, text in
                let p = picked[i]
                let wrong = p != nil && !(p!.correct)
                let isRight = (p?.correct ?? false) || (done && right.contains(i))
                let dim = done && p == nil && !right.contains(i)
                Button {
                    Task { await act { try await API.shared.post("answer", ["lesson": m.id, "k": v.k, "response": i]) } }
                } label: {
                    HStack(alignment: .firstTextBaseline, spacing: 10) {
                        Text(String(UnicodeScalar(65 + i)!)).font(Theme.mono(11)).foregroundStyle(Theme.muted).frame(width: 12)
                        Text(inline(text, .book(15.5, color: wrong ? Theme.muted : Theme.ink)))
                            .strikethrough(wrong, color: Theme.fail)
                            .multilineTextAlignment(.leading)
                        Spacer(minLength: 0)
                    }
                    .padding(.horizontal, 11).padding(.vertical, 8)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(isRight ? Theme.passSoft : wrong ? .clear : Theme.paper)
                    .overlay(RoundedRectangle(cornerRadius: 7).stroke(isRight ? Theme.pass : wrong ? Theme.fail : Theme.hairline))
                    .opacity(dim ? 0.55 : 1)
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier("opt-\(i)")
                .disabled(done || wrong || busy)
                if let why = p?.why, !why.isEmpty {
                    Prose(blocks: why, book: true, size: 15)
                        .padding(.leading, 10)
                        .overlay(alignment: .leading) { Rectangle().fill((p?.correct ?? false) ? Theme.pass : Theme.fail).frame(width: 2) }
                        .padding(.leading, 32)
                        .padding(.vertical, 2)
                }
            }
        }
    }
}

struct TypedBody: View {
    let m: LessonModel
    let v: StepView
    let act: (@escaping () async throws -> Advance) async -> Void
    @State private var text = ""
    @State private var invalid: Blocks? = nil
    @State private var busy = false
    @FocusState private var focused: Bool
    @Environment(Toast.self) private var toast

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            if !v.isDone {
                HStack(spacing: 8) {
                    TextField(v.placeholder?.isEmpty == false ? v.placeholder! : (v.kind == "numeric" ? "a number: 2e5, 4*10^10, 2^20 …" : "your answer"), text: $text)
                        .font(Theme.mono(14))
                        .autocorrectionDisabled()
                        .textInputAutocapitalization(.never)
                        .keyboardType(v.kind == "numeric" ? .asciiCapable : .default)
                        .focused($focused)
                        .submitLabel(.go)
                        .onSubmit { go() }
                        .padding(.horizontal, 9).padding(.vertical, 7)
                        .background(Theme.paper)
                        .overlay(RoundedRectangle(cornerRadius: 6).stroke(focused ? Theme.accent : Theme.hairline))
                    if let u = v.unit, !u.isEmpty {
                        Text(u).font(Theme.sans(12.5)).foregroundStyle(Theme.muted)
                    }
                    Button("check") { go() }.buttonStyle(Prominent()).disabled(busy)
                }
                if let inv = invalid {
                    Prose(blocks: inv, color: Theme.fail, size: 13)
                }
            }
            let rs = v.responses ?? []
            if !rs.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    ForEach(Array(rs.enumerated()), id: \.offset) { _, r in
                        HStack(alignment: .firstTextBaseline, spacing: 10) {
                            Text(r.correct ? "✓" : "✗").font(Theme.sans(13)).foregroundStyle(r.correct ? Theme.pass : Theme.fail).frame(width: 14)
                            Text(r.text).font(Theme.mono(12.5)).foregroundStyle(Theme.ink)
                            if let f = r.feedback, !f.isEmpty { Prose(blocks: f, color: Theme.muted, size: 13) }
                        }
                    }
                }
                .padding(.top, 2)
            }
        }
    }

    private func go() {
        let t = text.trimmingCharacters(in: .whitespaces)
        guard !t.isEmpty else { focused = true; return }
        busy = true
        Task {
            defer { busy = false }
            do {
                let r: Advance = try await API.shared.post("answer", ["lesson": m.id, "k": v.k, "response": text])
                if r.result?.invalid ?? false {
                    invalid = r.result?.feedback ?? [Block(type: "paragraph", text: "That did not parse.")]
                    focused = true
                    return
                }
                invalid = nil
                await m.apply(r, toast: toast)
                if !(r.result?.correct ?? false) { text = ""; focused = true }
            } catch { toast.show(error.localizedDescription) }
        }
    }
}

struct ReflectBody: View {
    let m: LessonModel
    let v: StepView
    let act: (@escaping () async throws -> Advance) async -> Void
    @State private var text = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            if !v.isDone {
                PlainTextArea(text: $text, placeholder: "Write your idea in a sentence or two, then compare with the tutor.", mono: false, height: 96)
                HStack {
                    Button("compare with the tutor") {
                        let t = text
                        Task { await act { try await API.shared.post("reflect", ["lesson": m.id, "k": v.k, "text": t]) } }
                    }.buttonStyle(Prominent())
                    Spacer()
                    Button("no idea yet · show me") {
                        Task { await act { try await API.shared.post("reflect", ["lesson": m.id, "k": v.k, "text": ""]) } }
                    }.buttonStyle(Bare())
                }
            } else {
                Text("you wrote").font(Theme.sans(11.5)).foregroundStyle(Theme.faint)
                Text((v.mine ?? "").isEmpty ? "(nothing: you asked to see it)" : v.mine!)
                    .font(Theme.book(15)).foregroundStyle(Theme.muted)
                    .padding(.leading, 10)
                    .overlay(alignment: .leading) { Rectangle().fill(Theme.hairline).frame(width: 2) }
                Text("the tutor").font(Theme.sans(11.5)).foregroundStyle(Theme.faint).padding(.top, 4)
                Prose(blocks: v.answer ?? [], book: true, size: 15.5)
                HStack(spacing: 8) {
                    Text("your version:").font(Theme.sans(11.5)).foregroundStyle(Theme.faint)
                    ForEach([("got", "had it"), ("partly", "partly"), ("missed", "missed it")], id: \.0) { k, label in
                        Button(label) {
                            Task {
                                if let r: StepOnly = try? await API.shared.post("reflect_self", ["lesson": m.id, "k": v.k, "self": k]) { m.replace(r.step) }
                            }
                        }
                        .buttonStyle(Outline(color: v.selfRating == k ? Theme.accent : Theme.ink, border: v.selfRating == k ? Theme.accent : Theme.hairline))
                    }
                }
                .padding(.top, 8)
            }
        }
    }
}

struct TryStep: View {
    let m: LessonModel
    let v: StepView
    let color: String
    @Environment(Toast.self) private var toast

    var body: some View {
        let done = v.isDone
        let solved = v.solved ?? false
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 8) {
                Text("▶").font(.system(size: 9)).foregroundStyle(Theme.codeNumber)
                Text("now solve it").font(Theme.sans(12)).foregroundStyle(Theme.muted)
            }
            HStack(alignment: .center, spacing: 12) {
                Balloon(color: color, solved: solved, size: 16)
                VStack(alignment: .leading, spacing: 2) {
                    Text(v.title ?? v.ref ?? "").font(Theme.sans(15, .medium)).foregroundStyle(Theme.ink)
                    HStack(spacing: 8) {
                        Text(v.difficulty ?? "").font(Theme.sans(11.5)).foregroundStyle(Theme.faint)
                        if solved { Text("✓ solved").font(Theme.sans(12.5)).foregroundStyle(Theme.pass) }
                        else if v.skipped ?? false { Text("skipped for now: it waits in the problem list").font(Theme.sans(12)).foregroundStyle(Theme.faint) }
                        else if let n = v.submits, n > 0 { Text(plural(n, "submission") + " so far").font(Theme.sans(12)).foregroundStyle(Theme.muted) }
                    }
                }
                Spacer()
            }
            HStack(spacing: 10) {
                if let ref = v.ref {
                    NavigationLink(value: Route.problem(ref)) { Text(solved ? "open" : "open problem →") }
                        .buttonStyle(done ? AnyButtonStyle(Outline()) : AnyButtonStyle(Prominent()))
                }
                if !done {
                    Button("later") {
                        Task {
                            do {
                                let r: Advance = try await API.shared.post("try_skip", ["lesson": m.id, "k": v.k])
                                await m.apply(r, toast: toast)
                            } catch { toast.show(error.localizedDescription) }
                        }
                    }.buttonStyle(Outline())
                }
            }
            if let note = v.note, !note.isEmpty {
                Prose(blocks: note, book: true, size: 15.5).padding(.top, 2)
            }
        }
        .padding(.horizontal, 16).padding(.vertical, 14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(done ? .clear : Theme.raised)
        .overlay(alignment: .leading) { Rectangle().fill(done ? Theme.hairline : Theme.codeNumber).frame(width: 3) }
        .clipShape(RoundedRectangle(cornerRadius: 9))
        .padding(.vertical, 12)
    }
}

struct AnyButtonStyle: ButtonStyle {
    private let make: (Configuration) -> AnyView
    init<S: ButtonStyle>(_ s: S) { make = { AnyView(s.makeBody(configuration: $0)) } }
    func makeBody(configuration: Configuration) -> some View { make(configuration) }
}
