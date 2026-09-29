import SwiftUI

struct ProblemScreen: View {
    let ref: String
    @State private var d: ProblemPayload? = nil
    @State private var error: String? = nil
    @State private var j: JudgeModel? = nil
    @State private var tab = ProcessInfo.processInfo.arguments.contains("-solve") ? "solve" : "statement"
    @State private var hints: [Blocks] = []
    @State private var editorial: Blocks? = nil
    @State private var solution: String? = nil
    @State private var submissions: [Submission] = []
    @State private var solved = false
    @State private var submits = 0
    @State private var graded = false
    @State private var srs: SRS? = nil
    @State private var gradeNote: String? = nil
    @State private var showGrade = false
    @Environment(Toast.self) private var toast
    @Environment(Armed.self) private var armed

    var body: some View {
        Group {
            if let d, let j {
                content(d, j)
            } else if let e = error {
                ErrorView(message: e) { await load() }
            } else {
                ProgressView().tint(Theme.muted).frame(maxWidth: .infinity, maxHeight: .infinity).background(Theme.paper)
            }
        }
        .task { await load() }
        .heartbeat()
        .navigationTitle(d?.title ?? "")
        .navigationBarTitleDisplayMode(.inline)
    }

    private func load() async {
        do {
            let p: ProblemPayload = try await API.shared.get("problem", ["ref": ref])
            d = p
            hints = p.hints ?? []
            editorial = p.editorial
            solution = p.solution
            submissions = p.submissions ?? []
            solved = p.solved ?? false
            submits = p.submits ?? 0
            graded = p.graded ?? false
            srs = p.srs
            if j == nil {
                j = JudgeModel(ref: ref, code: p.code, sampleInput: p.samples.first?.input ?? "", contest: false)
            }
            error = nil
        } catch {
            if d == nil { self.error = error.localizedDescription }
        }
    }

    private func content(_ d: ProblemPayload, _ j: JudgeModel) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                header(d)
                Picker("", selection: $tab) {
                    Text("statement").tag("statement")
                    Text("solve").tag("solve")
                }
                .pickerStyle(.segmented)
                .padding(.vertical, 12)
                if tab == "statement" { statement(d) } else { work(d, j) }
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

    private func header(_ d: ProblemPayload) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                if let l = d.lesson {
                    NavigationLink(value: Route.lesson(l)) {
                        Text("\(l) · \(d.lessonTitle ?? "")").font(Theme.sans(12)).foregroundStyle(Theme.muted).lineLimit(1)
                    }
                }
                Spacer()
                HStack(spacing: 5) {
                    ForEach(d.siblings ?? []) { s in
                        NavigationLink(value: Route.problem(s.ref)) {
                            Balloon(color: s.color, solved: s.solved, size: 10)
                                .padding(3)
                                .overlay(RoundedRectangle(cornerRadius: 3).stroke(s.ref == ref ? Theme.hairline : .clear))
                        }
                        .disabled(s.ref == ref)
                    }
                }
            }
            HStack(alignment: .firstTextBaseline, spacing: 10) {
                Balloon(color: d.color ?? "#888888", solved: solved, size: 18)
                Text(d.title).font(Theme.sans(24)).foregroundStyle(Theme.ink)
                Spacer()
                Text(solved ? "solved" : submits > 0 ? plural(submits, "submission") : "")
                    .font(Theme.sans(12)).foregroundStyle(solved ? Theme.pass : Theme.faint)
            }
            HStack(spacing: 14) {
                Text("time limit \(d.timeLimit ?? 1, format: .number) s")
                Text(d.difficulty ?? "")
                if let s = d.source, !s.isEmpty { Text(s).lineLimit(1) }
                if solved, let c = d.complexity, !c.isEmpty { Text("target \(c)") }
            }
            .font(Theme.sans(11.5)).foregroundStyle(Theme.faint)
        }
    }

    @ViewBuilder
    private func statement(_ d: ProblemPayload) -> some View {
        Prose(blocks: d.statement, book: true)
        SectionHeading(title: "input")
        Prose(blocks: d.input, book: true).padding(.top, 6)
        SectionHeading(title: "output")
        Prose(blocks: d.output, book: true).padding(.top, 6)
        SectionHeading(title: "samples")
        SamplesView(samples: d.samples)

        let total = d.hintsTotal ?? 0
        HStack {
            if total > 0 {
                Button(hints.count < total ? "hint \(hints.count + 1) of \(total)" : "no more hints") {
                    Task {
                        if let r: HintsPayload = try? await API.shared.post("hint", ["ref": ref]) { hints = r.hints }
                    }
                }
                .buttonStyle(Outline()).disabled(hints.count >= total)
            }
            Spacer()
            if editorial == nil {
                Button("read the editorial (counts as giving up)") {
                    guard armed.twice("editorial", toast, "Tap again to read the editorial. The next review of this problem will treat it as not solved alone.") else { return }
                    Task {
                        if let r: EditorialPayload = try? await API.shared.post("editorial", ["ref": ref]) {
                            editorial = r.editorial; solution = r.solution
                            if r.learned ?? false { toast.show("Lesson learned ✓") }
                        }
                    }
                }.buttonStyle(Bare())
            }
        }
        .padding(.top, 16)
        ForEach(Array(hints.enumerated()), id: \.offset) { i, h in
            SectionHeading(title: "hint \(i + 1)", rule: false)
            Prose(blocks: h, book: true, size: 16)
        }
        if let e = editorial {
            SectionHeading(title: "editorial")
            Prose(blocks: e, book: true, size: 16).padding(.top, 6)
            if let s = solution {
                DisclosureGroup { CodeBlock(text: s, size: 12).padding(.top, 6) } label: {
                    Text("reference solution").font(Theme.sans(12.5)).foregroundStyle(Theme.muted)
                }
                .tint(Theme.muted)
                .padding(.top, 10)
            }
        }
        subsList
    }

    @ViewBuilder
    private var subsList: some View {
        if !submissions.isEmpty {
            SectionHeading(title: "your submissions")
            VStack(spacing: 0) {
                ForEach(submissions) { s in
                    Row {
                        VerdictTag(verdict: s.verdict)
                        Text((s.failed ?? "").isEmpty ? "\(s.passed ?? 0)/\(s.total ?? 0)" : "on \(s.failed!)").font(Theme.sans(12)).foregroundStyle(Theme.muted)
                        Spacer()
                        Chip(text: "\(s.ms ?? 0) ms · \(whenAgo(s.ts))")
                    }
                }
            }
            .padding(.horizontal, -10)
        }
    }

    @ViewBuilder
    private func work(_ d: ProblemPayload, _ j: JudgeModel) -> some View {
        JudgePanel(j: j, color: d.color ?? "#888888") { r, mode in
            if let st = r.state { solved = st.solved ?? solved; submits = st.submits ?? submits }
            guard mode == "submit" else { return }
            Task {
                if let p: ProblemPayload = try? await API.shared.get("problem", ["ref": ref]) {
                    submissions = p.submissions ?? []
                    if r.result.verdict == "AC" { editorial = p.editorial; solution = p.solution }
                }
            }
            guard r.result.verdict == "AC" else { return }
            if r.learned ?? false { toast.show("Lesson learned ✓") }
            srs = r.srs
            if !graded || (r.srs?.isDue ?? false) { showGrade = true; gradeNote = nil }
            else { showGrade = false; gradeNote = "Scheduled: the next re-solve is on \(shortDate(r.srs?.due))." }
        }
        if showGrade { gradeBox }
        if let n = gradeNote {
            Text(n).font(Theme.sans(12.5)).foregroundStyle(Theme.muted).padding(.top, 8)
        }
        if let p = d.path {
            Text("also at " + p.replacingOccurrences(of: #"^.*/workspace/"#, with: "workspace/", options: .regularExpression))
                .font(Theme.sans(11.5)).foregroundStyle(Theme.faint).padding(.top, 10)
        }
        subsList
    }

    private var gradeBox: some View {
        VStack(alignment: .leading, spacing: 8) {
            SectionHeading(title: "how did that solve feel?", value: "schedules the re-solve")
            HStack(spacing: 8) {
                ForEach([(1, "hard"), (2, "good"), (3, "easy")], id: \.0) { feel, label in
                    Button(label) {
                        Task {
                            do {
                                let r: GradePayload = try await API.shared.post("grade_problem", ["ref": ref, "feel": feel])
                                toast.show("re-solve in " + plural(r.interval, "day"))
                                graded = true
                                showGrade = false
                                gradeNote = "Scheduled: re-solve on \(shortDate(r.due))."
                            } catch { toast.show(error.localizedDescription) }
                        }
                    }.buttonStyle(Outline())
                }
            }
        }
    }
}
