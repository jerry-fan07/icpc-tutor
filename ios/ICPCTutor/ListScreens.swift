import SwiftUI

// MARK: - lessons

struct LessonsScreen: View {
    var body: some View {
        Loader(load: { try await API.shared.get("lessons") as LessonsPayload }) { d, _ in
            Screen {
                let n = d.tracks.reduce(0) { $0 + $1.lessons.count }
                TitleLine(title: "lessons", note: "\(n) lessons in \(d.tracks.count) tracks")
                ForEach(d.tracks) { t in
                    let learned = t.lessons.filter { $0.status == "learned" }.count
                    SectionHeading(title: t.name, value: "\(learned) of \(t.lessons.count) learned")
                    if let b = t.blurb {
                        Text(b).font(Theme.sans(13)).foregroundStyle(Theme.muted).padding(.vertical, 6)
                    }
                    VStack(spacing: 0) {
                        ForEach(t.lessons) { l in lessonRow(l) }
                    }
                    .padding(.horizontal, -10)
                }
            }
        }
        .navigationTitle("lessons")
        .navigationBarTitleDisplayMode(.inline)
    }

    private func lessonRow(_ l: LessonRow) -> some View {
        let ahead = l.status == "new" && !(l.missing ?? []).isEmpty
        let status = ahead ? "ahead" : (l.status ?? "new")
        return RowLink(route: .lesson(l.id)) {
            StatusDot(status: status)
            Text(l.id).font(Theme.mono(11.5)).foregroundStyle(Theme.faint).frame(width: 44, alignment: .leading)
            VStack(alignment: .leading, spacing: 2) {
                Text(l.title).font(Theme.sans(14)).foregroundStyle(ahead ? Theme.muted : Theme.ink).lineLimit(2)
                HStack(spacing: 8) {
                    if let due = l.due, due > 0 {
                        Text("\(due) due").font(Theme.sans(11.5)).foregroundStyle(Theme.accent)
                    }
                    Text(l.status == "new"
                         ? (ahead ? "after " + (l.missing ?? []).prefix(2).joined(separator: ", ") : "~\(l.minutes ?? 0) min")
                         : "\(l.answered ?? 0)/\(l.questions ?? 0) · \(l.solved ?? 0)/\(l.problems ?? 0) solved")
                        .font(Theme.sans(11.5)).foregroundStyle(Theme.faint)
                }
            }
            Spacer(minLength: 4)
            BalloonRow(balloons: l.balloons ?? [])
        }
    }
}

// MARK: - problems

struct ProblemsScreen: View {
    @State private var mode = "all"

    var body: some View {
        Loader(load: { try await API.shared.get("problems") as ProblemsPayload }) { d, _ in
            let all = d.groups.flatMap { $0.lessons.flatMap { $0.problems } }
            Screen {
                TitleLine(title: "problems", note: "\(all.filter { $0.solved ?? false }.count) of \(all.count) solved")
                Tabs(options: [("all", "all"), ("open", "unsolved"), ("solved", "solved"), ("due", "due for re-solve")], selected: $mode)
                    .padding(.top, 14)
                let groups = filtered(d.groups)
                if groups.isEmpty {
                    Text("Nothing here.").font(Theme.sans(14)).foregroundStyle(Theme.faint).padding(.top, 20)
                }
                ForEach(groups) { g in
                    SectionHeading(title: g.name, value: "\(g.lessons.reduce(0) { $0 + $1.problems.count }) problems")
                    ForEach(g.lessons) { l in
                        NavigationLink(value: Route.lesson(l.id)) {
                            Text("\(l.id) · \(l.title)").font(Theme.sans(12)).foregroundStyle(Theme.faint)
                        }
                        .padding(.top, 12).padding(.bottom, 2)
                        VStack(spacing: 0) {
                            ForEach(l.problems) { p in ProblemRowView(p: p) }
                        }
                        .padding(.horizontal, -10)
                    }
                }
            }
        }
        .navigationTitle("problems")
        .navigationBarTitleDisplayMode(.inline)
    }

    private func filtered(_ groups: [ProblemGroup]) -> [ProblemGroup] {
        groups.compactMap { g in
            let lessons = g.lessons.compactMap { l -> ProblemGroupLesson? in
                let ps = l.problems.filter { p in
                    switch mode {
                    case "open": return !(p.solved ?? false)
                    case "solved": return p.solved ?? false
                    case "due": return p.due ?? false
                    default: return true
                    }
                }
                return ps.isEmpty ? nil : ProblemGroupLesson(id: l.id, title: l.title, status: l.status, problems: ps)
            }
            return lessons.isEmpty ? nil : ProblemGroup(track: g.track, name: g.name, lessons: lessons)
        }
    }
}

struct ProblemRowView: View {
    let p: ProblemRow
    var body: some View {
        let solved = p.solved ?? false
        RowLink(route: .problem(p.ref)) {
            Balloon(color: p.color ?? "#888888", solved: solved, size: 10)
            VStack(alignment: .leading, spacing: 2) {
                Text(p.title).font(Theme.sans(14)).foregroundStyle(Theme.ink).lineLimit(1)
                if let s = p.source, !s.isEmpty {
                    Text(s).font(Theme.sans(11.5)).foregroundStyle(Theme.faint).lineLimit(1)
                }
            }
            Spacer(minLength: 4)
            if p.due ?? false {
                Text("re-solve due").font(Theme.sans(11.5)).foregroundStyle(Theme.accent).fixedSize()
            }
            let d = p.difficulty ?? ""
            let n = p.submits ?? 0
            Text(solved ? "✓ \(d)" : n > 0 ? "\(n) \(n == 1 ? "try" : "tries") · \(d)" : d)
                .font(Theme.sans(12)).foregroundStyle(Theme.faint).fixedSize()
        }
    }
}

// MARK: - review

struct ReviewScreen: View {
    var body: some View {
        Loader(load: { try await API.shared.get("due") as DuePayload }) { d, _ in
            let cards = d.queue.filter { $0.kind == "card" }
            let probs = d.queue.filter { $0.kind == "problem" }
            Screen {
                if d.queue.isEmpty {
                    TitleLine(title: "review", note: "nothing due")
                    Text("The queue is empty. Cards you rate at the end of a lesson, and problems you rate after solving them, come back here when they are due.")
                        .font(Theme.sans(14)).foregroundStyle(Theme.faint).padding(.top, 16)
                } else {
                    TitleLine(title: "review", note: "\(d.queue.count) due")
                    if !probs.isEmpty {
                        SectionHeading(title: "re-solve from scratch", value: "\(probs.count)")
                        Text("Reset the editor and solve it again without looking. Rate it after the AC.")
                            .font(Theme.sans(13)).foregroundStyle(Theme.muted).padding(.vertical, 6)
                        VStack(spacing: 0) {
                            ForEach(probs) { q in
                                if let p = q.problem {
                                    RowLink(route: .problem(p.ref)) {
                                        Balloon(color: p.color ?? "#888888", solved: true, size: 10)
                                        Text(p.title).font(Theme.sans(14)).foregroundStyle(Theme.ink).lineLimit(1)
                                        Spacer()
                                        Chip(text: q.lessonTitle ?? q.lesson)
                                    }
                                }
                            }
                        }
                        .padding(.horizontal, -10)
                    }
                    if !cards.isEmpty {
                        SectionHeading(title: "cards", value: "\(cards.count)")
                        ForEach(cards) { q in
                            if let c = q.card { CardBlock(card: c) }
                        }
                    }
                }
            }
        }
        .heartbeat()
        .navigationTitle("review")
        .navigationBarTitleDisplayMode(.inline)
    }
}

/// A review card: question, then the answer, then the four ratings with their intervals.
struct CardBlock: View {
    let card: CardView
    @Environment(Toast.self) private var toast
    @State private var shown = false
    @State private var rated: String? = nil

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Prose(blocks: card.q, size: 15)
            HStack {
                if !shown && rated == nil {
                    Button("show answer") { withAnimation { shown = true } }.buttonStyle(Outline())
                }
                Spacer()
                Text(rated ?? (card.seen ? ((card.isDue ?? false) ? "due" : "next " + shortDate(card.due)) : "new"))
                    .font(Theme.sans(12)).foregroundStyle(Theme.faint)
            }
            if shown {
                Prose(blocks: card.a, size: 15)
                if rated == nil {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("how well did you know it?").font(Theme.sans(12)).foregroundStyle(Theme.faint)
                        HStack(spacing: 6) {
                            ForEach(Array(["again", "hard", "good", "easy"].enumerated()), id: \.offset) { i, label in
                                Button {
                                    Task {
                                        do {
                                            let r: GradePayload = try await API.shared.post("grade_card", ["lesson": card.lesson, "item": card.item, "rating": i + 1])
                                            toast.show("next review in " + plural(r.interval, "day"))
                                            withAnimation { rated = "next " + shortDate(r.due); shown = false }
                                        } catch { toast.show(error.localizedDescription) }
                                    }
                                } label: {
                                    HStack(spacing: 4) {
                                        Text(label)
                                        Text("\(card.intervals?[safe: i] ?? 0)d").font(Theme.mono(10.5)).opacity(0.7)
                                    }
                                }
                                .buttonStyle(Outline())
                            }
                        }
                    }
                }
            }
        }
        .padding(14)
        .background(Theme.paper)
        .overlay(RoundedRectangle(cornerRadius: 9).stroke(Theme.hairline))
        .padding(.top, 10)
    }
}

extension Array {
    subscript(safe i: Int) -> Element? { indices.contains(i) ? self[i] : nil }
}

// MARK: - stats

struct StatsScreen: View {
    var body: some View {
        Loader(load: { try await API.shared.get("stats") as Stats }) { s, _ in
            Screen {
                TitleLine(title: "stats", note: "\(s.hours.formatted()) h in sessions")
                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], alignment: .leading, spacing: 18) {
                    Figure(n: "\(s.solved)", k: "problems solved")
                    Figure(n: "\(s.streak)", k: "day streak")
                    Figure(n: "\(s.firstTryPct)%", k: "questions right first try")
                    Figure(n: "\(s.submissions)", k: "submissions")
                }
                .padding(.top, 18)

                let order = ["AC", "WA", "TLE", "RE", "CE", "OLE"]
                let total = s.verdicts.values.reduce(0, +)
                SectionHeading(title: "verdicts", value: total > 0 ? "\(Int((100.0 * Double(s.verdicts["AC"] ?? 0) / Double(total)).rounded()))% accepted" : "")
                if total > 0 {
                    GeometryReader { g in
                        HStack(spacing: 0) {
                            ForEach(order.filter { (s.verdicts[$0] ?? 0) > 0 }, id: \.self) { v in
                                Rectangle().fill(Theme.verdictColor(v).opacity(v == "AC" ? 0.8 : v == "CE" ? 0.5 : 0.85))
                                    .frame(width: g.size.width * Double(s.verdicts[v] ?? 0) / Double(total))
                            }
                        }
                    }
                    .frame(height: 10)
                    .clipShape(RoundedRectangle(cornerRadius: 3))
                    .padding(.top, 8)
                    HStack(spacing: 14) {
                        ForEach(order.filter { (s.verdicts[$0] ?? 0) > 0 }, id: \.self) { v in
                            HStack(spacing: 4) { VerdictTag(verdict: v).frame(minWidth: 0); Text("\(s.verdicts[v] ?? 0)").font(Theme.sans(12)).foregroundStyle(Theme.muted) }
                        }
                    }
                    .padding(.top, 6)
                } else {
                    Text("No submissions yet.").font(Theme.sans(14)).foregroundStyle(Theme.faint).padding(.top, 8)
                }

                SectionHeading(title: "progress")
                ForEach(s.tracks) { t in
                    progress("\(t.name): lessons learned", t.learned, t.total)
                    progress("\(t.name): problems solved", t.solved, t.problems)
                }
                progress("cards scheduled", s.cardsSeen, s.cardsTotal)

                SectionHeading(title: "activity", value: "last \(s.activityWeeks) weeks")
                ActivityGrid(counts: s.activity, weeks: s.activityWeeks)

                SectionHeading(title: "due · next 14 days", value: "\(s.forecast.reduce(0, +))", rule: false)
                ForecastStrip(counts: s.forecast)

                if !s.retention.isEmpty {
                    SectionHeading(title: "retention by lesson")
                    ForEach(s.retention) { Meter(label: $0.label, pct: $0.pct) }
                }
                if !s.hardest.isEmpty {
                    SectionHeading(title: "hardest for you")
                    VStack(spacing: 0) {
                        ForEach(s.hardest) { h in
                            RowLink(route: h.ref.map { Route.problem($0) } ?? .lesson(h.lesson)) {
                                StatusDot(status: "new")
                                Text(h.label).font(Theme.sans(13)).foregroundStyle(Theme.ink).lineLimit(1)
                                Spacer()
                                Text(h.ease.formatted()).font(Theme.mono(11.5)).foregroundStyle(Theme.faint)
                            }
                        }
                    }
                    .padding(.horizontal, -10)
                }
            }
        }
        .navigationTitle("stats")
        .navigationBarTitleDisplayMode(.inline)
    }

    private func progress(_ label: String, _ done: Int, _ total: Int) -> some View {
        VStack(alignment: .leading, spacing: 5) {
            HStack {
                Text(label).font(Theme.sans(13)).foregroundStyle(Theme.ink)
                Spacer()
                Text("\(done) / \(total)").font(Theme.sans(11.5)).foregroundStyle(Theme.faint)
            }
            Bar(fraction: total > 0 ? Double(done) / Double(total) : 0)
        }
        .padding(.vertical, 7)
    }
}

struct ActivityGrid: View {
    let counts: [Int]
    let weeks: Int
    var body: some View {
        let peak = max(1, counts.max() ?? 1)
        LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 3), count: max(1, weeks)), spacing: 3) {
            ForEach(Array(counts.enumerated()), id: \.offset) { _, n in
                RoundedRectangle(cornerRadius: 2)
                    .fill(n > 0 ? Theme.accent.opacity(0.35 + 0.65 * min(1, Double(n) / Double(peak))) : Theme.hairline)
                    .frame(height: 10)
            }
        }
        .padding(.top, 10)
    }
}

// MARK: - notebook

struct NotebookScreen: View {
    @AppStorage("cp.nb.which") private var which = "mine"

    var body: some View {
        Loader(load: { try await API.shared.get("notebook") as NotebookPayload }) { d, _ in
            Screen {
                let n = d.lessons.reduce(0) { $0 + $1.problems.count }
                TitleLine(title: "notebook", note: plural(n, "solved problem"))
                Text("The code of everything you have solved, lesson by lesson: the seed of a team reference document.")
                    .font(Theme.sans(13)).foregroundStyle(Theme.muted).padding(.top, 8)
                Tabs(options: [("mine", "my accepted code"), ("ref", "reference solutions")], selected: $which)
                    .padding(.top, 12)
                if d.lessons.isEmpty {
                    Text("Solve a problem and it lands here. At an ICPC contest you may bring a printed team reference document; this is the start of yours.")
                        .font(Theme.sans(14)).foregroundStyle(Theme.faint).padding(.top, 20)
                }
                ForEach(d.lessons) { l in
                    Text("\(l.id) · \(l.title)").font(Theme.sans(17, .medium)).foregroundStyle(Theme.ink)
                        .padding(.top, 30).padding(.bottom, 4)
                    ForEach(l.problems) { p in
                        let mine = which == "mine" && p.mine != nil
                        let code = mine ? (p.mine ?? "") : p.reference
                        HStack(spacing: 8) {
                            Balloon(color: p.color, solved: true, size: 10)
                            NavigationLink(value: Route.problem(p.ref)) {
                                Text(p.title).font(Theme.sans(13.5, .medium)).foregroundStyle(Theme.ink)
                            }
                            Text([p.complexity ?? "", which == "mine" && p.mine == nil ? "reference (no accepted copy saved)" : which == "mine" ? "your accepted code" : "reference"]
                                .filter { !$0.isEmpty }.joined(separator: " · "))
                                .font(Theme.sans(11.5)).foregroundStyle(Theme.faint).lineLimit(1)
                        }
                        .padding(.top, 14).padding(.bottom, 6)
                        CodeBlock(text: code, size: 12)
                    }
                }
            }
        }
        .navigationTitle("notebook")
        .navigationBarTitleDisplayMode(.inline)
    }
}

// MARK: - settings / about

struct SettingsScreen: View {
    @AppStorage(API.urlKey) private var url = API.defaultURL
    @State private var status: String? = nil
    @State private var env: Env? = nil
    @State private var checking = false

    var body: some View {
        Screen {
            TitleLine(title: "settings", note: "the server on your Mac")
            Text("Everything lives on the Mac: the lessons, your progress, your code, and the C++ compiler that judges it. The phone talks to it over Wi-Fi. On the Mac run:")
                .font(Theme.sans(14)).foregroundStyle(Theme.ink).padding(.top, 14)
            CodeBlock(text: "python3 cp.py serve --host 0.0.0.0", lang: "text", size: 12.5).padding(.top, 8)
            Text("and type the address it prints here. The Mac's name usually works; its IP address always does.")
                .font(Theme.sans(13)).foregroundStyle(Theme.muted).padding(.top, 8)

            SectionHeading(title: "server address")
            TextField("http://your-mac.local:8000", text: $url)
                .font(Theme.mono(14))
                .keyboardType(.URL)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .padding(.horizontal, 10).padding(.vertical, 8)
                .background(Theme.raised)
                .overlay(RoundedRectangle(cornerRadius: 6).stroke(Theme.hairline))
                .padding(.top, 6)
                .onSubmit { Task { await check() } }
            HStack {
                Button(checking ? "checking…" : "check connection") { Task { await check() } }
                    .buttonStyle(Outline()).disabled(checking)
                Spacer()
                if let s = status {
                    Text(s).font(Theme.sans(12.5)).foregroundStyle(s.hasPrefix("ok") ? Theme.pass : Theme.fail).lineLimit(2)
                }
            }
            .padding(.top, 10)

            if let e = env {
                SectionHeading(title: "the Mac")
                Grid(alignment: .leading, horizontalSpacing: 14, verticalSpacing: 8) {
                    GridRow {
                        Text("compiler").font(Theme.sans(13)).foregroundStyle(Theme.faint)
                        Text(e.compiler.ok ? (e.compiler.version ?? "") : (e.compiler.error ?? "none"))
                            .font(Theme.sans(13)).foregroundStyle(e.compiler.ok ? Theme.ink : Theme.fail)
                    }
                    GridRow {
                        Text("progress").font(Theme.sans(13)).foregroundStyle(Theme.faint)
                        Text(e.progress ?? "").font(Theme.mono(11.5)).foregroundStyle(Theme.ink)
                    }
                    GridRow {
                        Text("your code").font(Theme.sans(13)).foregroundStyle(Theme.faint)
                        Text((e.workspace ?? "") + "/<lesson>/<problem>.cpp").font(Theme.mono(11.5)).foregroundStyle(Theme.ink)
                    }
                }
                .padding(.top, 8)
                if let errs = e.loadErrors, !errs.isEmpty {
                    ForEach(errs.sorted(by: { $0.key < $1.key }), id: \.key) { k, v in WarnBox(text: "\(k): \(v)") }
                }
            }

            SectionHeading(title: "about")
            Prose(blocks: [
                Block(type: "paragraph", text: "Two tracks. **C++ for contests** teaches the language by contrast with Python: what C++ does differently and which differences cost points. **Algorithms, from the question up** rebuilds each technique from a concrete problem: the brute force, what it wastes, the insight, why it is correct, then the code."),
                Block(type: "paragraph", text: "Lessons are dialogues. The page shows everything up to the next question and waits. Wrong options say *why* they are wrong; that is where most of the teaching is. `show me` is always there, and nothing is locked."),
                Block(type: "paragraph", text: "Problems are judged like an ICPC contest: your file is compiled with GCC on the Mac, run on every test with a time limit, and the first failure is the verdict. Cards at the end of a lesson, and problems after you solve them, come back in **review** on an SM-2 schedule."),
            ], book: true, size: 16)
            .padding(.top, 10)
            Text("Submitted code runs on the Mac without a sandbox. Only bind the server to 0.0.0.0 on a network you trust, such as your home Wi-Fi.")
                .font(Theme.sans(12.5)).foregroundStyle(Theme.faint).padding(.top, 14)
        }
        .navigationTitle("settings")
        .navigationBarTitleDisplayMode(.inline)
        .task { await check() }
    }

    private func check() async {
        checking = true
        defer { checking = false }
        do {
            let e: Env = try await API.shared.get("env")
            env = e
            status = "ok · " + (e.compiler.ok ? (e.compiler.version ?? "compiler found").split(separator: " ").prefix(2).joined(separator: " ") : "no compiler")
        } catch {
            env = nil
            status = error.localizedDescription
        }
    }
}
