import SwiftUI

/// The countdown; re-renders every second and reloads the screen when time runs out.
struct ContestClock: View {
    let remaining: Int
    let loadedAt: Date
    var size: CGFloat = 24
    var onExpire: (() -> Void)? = nil
    var body: some View {
        TimelineView(.periodic(from: loadedAt, by: 1)) { ctx in
            let left = remaining - Int(ctx.date.timeIntervalSince(loadedAt))
            Text(clock(left))
                .font(Theme.mono(size)).monospacedDigit()
                .foregroundStyle(left < 600 ? Theme.fail : Theme.ink)
                .onChange(of: left <= 0) { _, expired in if expired { onExpire?() } }
        }
    }
}

struct ScoreCell: View {
    let r: ContestRow
    var body: some View {
        if r.solved {
            HStack(spacing: 3) {
                Text("+\(r.wrong ?? 0 > 0 ? "\(r.wrong!)" : "")").font(Theme.mono(13)).foregroundStyle(Theme.pass)
                Text("\(r.minute ?? 0)′").font(Theme.mono(12)).foregroundStyle(Theme.faint)
            }
        } else if let w = r.wrong, w > 0 {
            Text("−\(w)").font(Theme.mono(13)).foregroundStyle(Theme.fail)
        } else {
            Text("·").font(Theme.mono(13)).foregroundStyle(Theme.faint)
        }
    }
}

struct Scoreboard: View {
    let c: ContestView
    let clickable: Bool
    var body: some View {
        VStack(spacing: 0) {
            ForEach(c.rows) { r in
                let inner = Row {
                    Text(r.letter).font(Theme.mono(13).weight(.semibold)).foregroundStyle(Theme.ink).frame(width: 18)
                    Balloon(color: r.color, solved: r.solved, size: 10)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(r.title).font(Theme.sans(14)).foregroundStyle(Theme.ink).lineLimit(1)
                        if let l = r.lesson {
                            Text("\(l) \(r.lessonTitle ?? "") · \(r.difficulty ?? "")").font(Theme.sans(11.5)).foregroundStyle(Theme.faint).lineLimit(1)
                        }
                    }
                    Spacer()
                    if let last = r.last, !r.solved, !last.isEmpty { VerdictTag(verdict: last).frame(minWidth: 0) }
                    ScoreCell(r: r).frame(width: 64, alignment: .trailing)
                }
                if clickable {
                    NavigationLink(value: Route.contestProblem(r.letter)) { inner }.buttonStyle(RowPress())
                } else if r.lesson != nil {
                    NavigationLink(value: Route.problem(r.ref)) { inner }.buttonStyle(RowPress())
                } else {
                    inner
                }
            }
        }
        .padding(.horizontal, -10)
    }
}

struct ContestScreen: View {
    @State private var minutes = 120
    @State private var count = 6
    @State private var pool = "studied"
    @Environment(Toast.self) private var toast
    @Environment(Armed.self) private var armed

    var body: some View {
        Loader(load: { try await API.shared.get("contest") as ContestPayload }) { s, reload in
            Screen {
                if let c = s.active {
                    active(c, reload)
                } else {
                    setup(s, reload)
                }
            }
        }
        .heartbeat()
        .navigationTitle("contest")
        .navigationBarTitleDisplayMode(.inline)
    }

    @ViewBuilder
    private func active(_ c: ContestView, _ reload: @escaping () async -> Void) -> some View {
        HStack(alignment: .firstTextBaseline) {
            Text("contest #\(c.id)").font(Theme.sans(26)).foregroundStyle(Theme.ink)
            Spacer()
            ContestClock(remaining: c.remaining, loadedAt: Date()) { Task { await reload() } }
        }
        HStack(spacing: 32) {
            Figure(n: "\(c.solved) / \(c.rows.count)", k: "solved")
            Figure(n: "\(c.penalty)", k: "penalty minutes")
            Figure(n: "\(c.elapsed / 60)′", k: "elapsed of \(c.minutes)′")
        }
        .padding(.top, 14)
        SectionHeading(title: "problems", value: "the order says nothing about difficulty")
        Scoreboard(c: c, clickable: true)
        Text("No hints, no editorials, no lesson names: recognising the technique is the skill. Hidden tests report only their verdict. Each rejected submission on a problem you later solve costs 20 minutes; compilation errors cost nothing.")
            .font(Theme.sans(12.5)).foregroundStyle(Theme.muted).padding(.top, 18)
        Button("end the contest now") {
            guard armed.twice("endcontest", toast, "Tap again to end the contest now.") else { return }
            Task { try? await API.shared.post("contest_end"); await reload() }
        }
        .buttonStyle(Bare()).padding(.top, 14)
    }

    @ViewBuilder
    private func setup(_ s: ContestPayload, _ reload: @escaping () async -> Void) -> some View {
        TitleLine(title: "virtual contest", note: s.past.isEmpty ? "ICPC rules, against the clock" : plural(s.past.count, "contest") + " so far")
        Prose(blocks: [Block(type: "paragraph", text: "A set of problems in random order, labelled A, B, C..., a clock, and ICPC scoring: most problems solved wins; ties are broken by penalty, the sum over solved problems of the minute of acceptance plus 20 minutes for each rejected submission before it. The problems come from lessons you have started, unsolved ones first, and their lessons stay hidden until the end.")], book: true, size: 16)
            .padding(.top, 12)
        VStack(alignment: .leading, spacing: 12) {
            segment("length", [(60, "1 h"), (120, "2 h"), (180, "3 h"), (300, "5 h")], $minutes)
            segment("problems", [(4, "4"), (6, "6"), (8, "8"), (10, "10")], $count)
            segmentS("from", [("studied", "lessons I have started"), ("algo", "the algorithms track"), ("all", "everything")], $pool)
        }
        .padding(.top, 18)
        Button("start the clock") {
            Task {
                do {
                    let _: ContestStarted = try await API.shared.post("contest_start", ["minutes": minutes, "count": count, "pool": pool])
                    await reload()
                } catch { toast.show(error.localizedDescription) }
            }
        }
        .buttonStyle(Prominent()).padding(.top, 20)
        if let last = s.last {
            SectionHeading(title: "last contest", value: "\(last.solved) solved · \(last.penalty) penalty")
            Scoreboard(c: last, clickable: false)
            Text("Now the lessons are shown: each problem links to its page and editorial.").font(Theme.sans(12.5)).foregroundStyle(Theme.muted).padding(.top, 8)
        }
        if s.past.count > 1 {
            SectionHeading(title: "history")
            VStack(spacing: 0) {
                ForEach(s.past) { p in
                    Row {
                        Text("#\(p.id)").font(Theme.mono(11.5)).foregroundStyle(Theme.faint).frame(width: 30, alignment: .leading)
                        Text("\(shortDate(p.started)) · \(p.minutes) min").font(Theme.sans(13)).foregroundStyle(Theme.ink)
                        Spacer()
                        Chip(text: "\(p.solved)/\(p.problems) solved · \(p.penalty) penalty")
                    }
                }
            }
            .padding(.horizontal, -10)
        }
    }

    private func segment(_ label: String, _ options: [(Int, String)], _ sel: Binding<Int>) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(label).font(Theme.sans(12.5)).foregroundStyle(Theme.muted)
            HStack(spacing: 6) {
                ForEach(options, id: \.0) { v, l in
                    Button(l) { sel.wrappedValue = v }
                        .buttonStyle(Outline(color: sel.wrappedValue == v ? Theme.pass : Theme.ink, border: sel.wrappedValue == v ? Theme.pass : Theme.hairline))
                }
            }
        }
    }

    private func segmentS(_ label: String, _ options: [(String, String)], _ sel: Binding<String>) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(label).font(Theme.sans(12.5)).foregroundStyle(Theme.muted)
            VStack(alignment: .leading, spacing: 6) {
                ForEach(options, id: \.0) { v, l in
                    Button(l) { sel.wrappedValue = v }
                        .buttonStyle(Outline(color: sel.wrappedValue == v ? Theme.pass : Theme.ink, border: sel.wrappedValue == v ? Theme.pass : Theme.hairline))
                }
            }
        }
    }
}

struct ContestProblemScreen: View {
    let letter: String
    @State private var c: ContestView? = nil
    @State private var d: ProblemPayload? = nil
    @State private var j: JudgeModel? = nil
    @State private var row: ContestRow? = nil
    @State private var subs: [ContestSub] = []
    @State private var error: String? = nil
    @State private var loadedAt = Date()
    @State private var tab = "statement"
    @State private var acNote: String? = nil
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        Group {
            if let c, let d, let j, let row {
                content(c, d, j, row)
            } else if let e = error {
                ErrorView(message: e) { await load() }
            } else {
                ProgressView().tint(Theme.muted).frame(maxWidth: .infinity, maxHeight: .infinity).background(Theme.paper)
            }
        }
        .task { await load() }
        .heartbeat()
        .navigationTitle("problem \(letter)")
        .navigationBarTitleDisplayMode(.inline)
    }

    private func load() async {
        do {
            let s: ContestPayload = try await API.shared.get("contest")
            guard let active = s.active else { error = "The contest is over."; return }
            guard let r = active.rows.first(where: { $0.letter == letter }) else { error = "no problem \(letter) in this contest"; return }
            let p: ProblemPayload = try await API.shared.get("problem", ["ref": r.ref, "contest": "1"])
            c = active; d = p; row = p.row ?? r; subs = p.subs ?? []; loadedAt = Date()
            if j == nil { j = JudgeModel(ref: r.ref, code: p.code, sampleInput: p.samples.first?.input ?? "", contest: true) }
            error = nil
        } catch {
            if d == nil { self.error = error.localizedDescription }
        }
    }

    private func content(_ c: ContestView, _ d: ProblemPayload, _ j: JudgeModel, _ row: ContestRow) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                HStack(spacing: 10) {
                    Text("contest #\(c.id)").font(Theme.sans(12)).foregroundStyle(Theme.muted)
                    Spacer()
                    ForEach(c.rows) { r in
                        NavigationLink(value: Route.contestProblem(r.letter)) {
                            Text(r.letter).font(Theme.mono(12)).foregroundStyle(r.letter == letter ? Theme.ink : Theme.faint)
                        }
                        .disabled(r.letter == letter)
                    }
                    ContestClock(remaining: c.remaining, loadedAt: loadedAt, size: 13) { dismiss() }
                }
                HStack(alignment: .firstTextBaseline, spacing: 10) {
                    Text(letter).font(Theme.mono(22)).foregroundStyle(Color(hex: d.color ?? "#888888"))
                    Text(d.title).font(Theme.sans(24)).foregroundStyle(Theme.ink)
                    Spacer()
                    ScoreCell(r: row)
                }
                .padding(.top, 8)
                Text("time limit \(d.timeLimit ?? 1, format: .number) s").font(Theme.sans(11.5)).foregroundStyle(Theme.faint).padding(.top, 4)
                Picker("", selection: $tab) {
                    Text("statement").tag("statement")
                    Text("solve").tag("solve")
                }
                .pickerStyle(.segmented)
                .padding(.vertical, 12)
                if tab == "statement" {
                    Prose(blocks: d.statement, book: true)
                    SectionHeading(title: "input")
                    Prose(blocks: d.input, book: true).padding(.top, 6)
                    SectionHeading(title: "output")
                    Prose(blocks: d.output, book: true).padding(.top, 6)
                    SectionHeading(title: "samples")
                    SamplesView(samples: d.samples)
                } else {
                    JudgePanel(j: j, color: d.color ?? "#888888") { r, mode in
                        guard mode == "submit", let cv = r.contest else { return }
                        self.c = cv
                        if let me = cv.rows.first(where: { $0.ref == row.ref }) {
                            self.row = me
                            if r.result.verdict == "AC" { acNote = "Accepted at minute \(me.minute ?? 0). Back to the scoreboard when you are ready." }
                        }
                        Task {
                            if let p: ProblemPayload = try? await API.shared.get("problem", ["ref": row.ref, "contest": "1"]) { subs = p.subs ?? [] }
                        }
                    }
                    if let n = acNote { Text(n).font(Theme.sans(12.5)).foregroundStyle(Theme.pass).padding(.top, 8) }
                }
                if !subs.isEmpty {
                    SectionHeading(title: "submissions")
                    VStack(spacing: 0) {
                        ForEach(subs) { x in
                            Row { VerdictTag(verdict: x.verdict); Spacer(); Chip(text: "minute \(x.minute)") }
                        }
                    }
                    .padding(.horizontal, -10)
                }
            }
            .padding(.horizontal, 18)
            .padding(.top, 8)
            .padding(.bottom, 60)
            .frame(maxWidth: 760)
            .frame(maxWidth: .infinity)
        }
        .background(Theme.paper)
        .scrollDismissesKeyboard(.interactively)
    }
}
