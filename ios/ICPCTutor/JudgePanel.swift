import SwiftUI

/// The editor, the buttons, custom input and the verdicts: shared by practice and
/// contest.  In a contest, hidden tests say only their verdict and custom input runs
/// your program alone.
@Observable
final class JudgeModel {
    let ref: String
    let contest: Bool
    var code: String
    var dirty = false
    var busy = false
    var mode = "submit"
    var startedAt: Date? = nil
    var run: RunPayload? = nil
    var runError: String? = nil
    var selectedCase: String? = nil
    var customOpen = false
    var stdin: String
    var custom: CustomResult? = nil
    var customError: String? = nil
    var customBusy = false
    var balloon: String? = nil
    var quiet = false          // a programmatic code change: not an edit to autosave
    private var saveTask: Task<Void, Never>? = nil

    init(ref: String, code: String, sampleInput: String, contest: Bool) {
        self.ref = ref
        self.code = code
        self.stdin = sampleInput
        self.contest = contest
    }

    func changed() {
        if quiet { quiet = false; return }
        dirty = true
        saveTask?.cancel()
        saveTask = Task {
            try? await Task.sleep(for: .seconds(1.5))
            if !Task.isCancelled { await save() }
        }
    }

    func save() async {
        guard dirty else { return }
        dirty = false
        try? await API.shared.post("code_save", ["ref": ref, "code": code])
    }

    @MainActor
    func submit(_ mode: String) async {
        guard !busy else { return }
        busy = true
        self.mode = mode
        saveTask?.cancel()
        dirty = false
        startedAt = Date()
        run = nil
        runError = nil
        defer { busy = false; startedAt = nil }
        do {
            let r: RunPayload = try await API.shared.post("run", ["ref": ref, "code": code, "mode": mode, "contest": contest], timeout: 240)
            run = r
            let cases = r.result.cases ?? []
            selectedCase = cases.first { $0.verdict != "AC" }?.name ?? (mode == "samples" ? cases.first?.name : nil)
        } catch {
            runError = error.localizedDescription
        }
    }

    @MainActor
    func runCustom() async {
        customBusy = true
        custom = nil
        customError = nil
        defer { customBusy = false }
        do {
            custom = try await API.shared.post("custom", ["ref": ref, "code": code, "input": stdin, "contest": contest], timeout: 240)
        } catch {
            customError = error.localizedDescription
        }
    }
}

struct JudgePanel: View {
    @Bindable var j: JudgeModel
    var color: String = "#888888"
    var onResult: ((RunPayload, String) -> Void)? = nil
    @Environment(Toast.self) private var toast
    @Environment(Armed.self) private var armed
    @Environment(\.scenePhase) private var phase

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            EditorBox(text: $j.code)
                .onChange(of: j.code) { _, _ in j.changed() }
            HStack(spacing: 8) {
                Button("submit") { Task { await j.submit("submit"); report() } }.buttonStyle(Prominent()).disabled(j.busy)
                Button("run samples") { Task { await j.submit("samples"); report() } }.buttonStyle(Outline()).disabled(j.busy)
                Button("custom input") { withAnimation { j.customOpen.toggle() } }
                    .buttonStyle(Outline(color: j.customOpen ? Theme.pass : Theme.ink, border: j.customOpen ? Theme.pass : Theme.hairline))
                Spacer()
                Button("reset") {
                    guard armed.twice("code", toast, "Tap again to replace your code with the starter.") else { return }
                    Task {
                        if let r: CodePayload = try? await API.shared.post("code_reset", ["ref": j.ref]) { j.quiet = true; j.code = r.code; j.dirty = false }
                    }
                }.buttonStyle(Bare())
            }
            if j.customOpen { customBox }
            results
        }
        .onDisappear { Task { await j.save() } }
        .onChange(of: phase) { _, p in if p != .active { Task { await j.save() } } }
        .overlay(alignment: .bottom) {
            if let b = j.balloon { FloatingBalloon(color: b).id(b + "\(Date().timeIntervalSince1970)") }
        }
    }

    private func report() {
        guard let r = j.run else { return }
        if j.mode == "submit", r.result.verdict == "AC", (r.firstAc ?? false) || j.contest {
            j.balloon = color
            Task { try? await Task.sleep(for: .seconds(3.4)); j.balloon = nil }
        }
        onResult?(r, j.mode)
    }

    // MARK: results

    @ViewBuilder
    private var results: some View {
        if let t0 = j.startedAt {
            TimelineView(.periodic(from: t0, by: 0.1)) { ctx in
                banner(title: j.mode == "submit" ? "judging…" : "running samples…",
                       sub: String(format: "%.1f s", ctx.date.timeIntervalSince(t0)), color: Theme.muted, soft: Theme.raised)
            }
        } else if let e = j.runError {
            Text(e).font(Theme.sans(13)).foregroundStyle(Theme.fail)
        } else if let r = j.run {
            resultView(r)
        }
    }

    private func banner(title: String, sub: String, color: Color, soft: Color) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(title).font(Theme.sans(17, .medium)).foregroundStyle(color)
            Text(sub).font(Theme.sans(12)).foregroundStyle(Theme.muted)
        }
        .padding(.horizontal, 14).padding(.vertical, 10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(soft)
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    @ViewBuilder
    private func resultView(_ r: RunPayload) -> some View {
        let res = r.result
        let v = res.verdict
        let samples = j.mode == "samples"
        var title = verdictName[v] ?? v
        let _ = { if v != "AC" && v != "CE", let f = res.failed, !f.isEmpty { title += " on \(f)" }; if samples && v == "AC" { title = "Samples pass" } }()
        let passed = res.passed ?? 0, total = res.total ?? 0
        let sub = v == "CE" ? "fix the first error; the rest often follow from it"
            : "\(passed) / \(total) passed" + (!samples && v != "AC" ? ", stopped at the first failure" : "")
              + " · max \(res.maxMs ?? 0) ms of \(Int((res.timeLimit ?? 1) * 1000)) · \(String(format: "%.1f", Double(res.maxKb ?? 0) / 1024)) MB"
        VStack(alignment: .leading, spacing: 10) {
            banner(title: title, sub: sub, color: Theme.verdictColor(v), soft: Theme.verdictSoft(v))
            if samples && v == "AC" {
                Text("Samples are only the start. Submit to run the hidden tests.").font(Theme.sans(12.5)).foregroundStyle(Theme.muted)
            }
            if v == "CE" {
                PreBox(text: res.compile ?? "", maxHeight: 400)
            } else {
                let cases = res.cases ?? []
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 5) {
                        ForEach(cases) { c in
                            Button { j.selectedCase = c.name } label: {
                                RoundedRectangle(cornerRadius: 3)
                                    .fill(Theme.verdictColor(c.verdict).opacity(c.verdict == "AC" ? 0.75 : 1))
                                    .frame(width: 18, height: 12)
                                    .overlay(RoundedRectangle(cornerRadius: 3).stroke(Theme.ink, lineWidth: j.selectedCase == c.name ? 1.5 : 0))
                            }
                            .buttonStyle(.plain)
                        }
                        ForEach(0..<max(0, total - cases.count), id: \.self) { _ in
                            RoundedRectangle(cornerRadius: 3).fill(Theme.hairline).frame(width: 18, height: 12)
                        }
                    }
                }
                if let c = cases.first(where: { $0.name == j.selectedCase }) { caseView(c) }
            }
            if let w = res.warnings, !w.isEmpty {
                DisclosureGroup { PreBox(text: w, maxHeight: 300) } label: {
                    Text("compiler warnings").font(Theme.sans(12.5)).foregroundStyle(Theme.muted)
                }
                .tint(Theme.muted)
            }
        }
    }

    private func caseView(_ c: JudgeCase) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 10) {
                VerdictTag(verdict: c.verdict)
                Text(c.name).font(Theme.sans(13, .medium)).foregroundStyle(Theme.ink)
                if let g = c.gen, !g.isEmpty { Chip(text: g) }
                Chip(text: "\(c.ms ?? 0) ms")
                Spacer()
            }
            if c.hidden ?? false {
                if c.verdict != "AC" {
                    Text("A hidden test. In a contest that is all the judge says: find the case yourself (edge cases, the limits, overflow, a brute force to compare against).")
                        .font(Theme.sans(12.5)).foregroundStyle(Theme.muted)
                }
            } else {
                if let msg = c.message, !msg.isEmpty {
                    Text(msg).font(Theme.sans(12.5)).foregroundStyle(c.verdict == "TLE" ? Theme.slow : Theme.fail)
                }
                if let n = c.note, !n.isEmpty, c.verdict != "AC" {
                    Text(n).font(Theme.sans(12.5)).foregroundStyle(Theme.muted)
                }
                if let inp = c.input, !inp.isEmpty {
                    ioBlock("input", inp)
                    ioBlock("expected", c.expected ?? "")
                    ioBlock("your output", c.got ?? "")
                } else if c.verdict != "AC" {
                    Text("This hidden test is large (\((c.inputSize ?? 0) / 1024) KB of input), so it is not shown. "
                         + (c.verdict == "TLE" ? "A time limit on a large test usually means the complexity, not a constant factor, is the problem."
                                               : "Test your program on big random inputs against a brute force."))
                        .font(Theme.sans(12.5)).foregroundStyle(Theme.muted)
                    if let g = c.got, !g.isEmpty { ioBlock("start of your output", g) }
                }
                if let e = c.stderr, !e.isEmpty { ioBlock("stderr", e) }
            }
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Theme.paper)
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(c.verdict == "AC" ? Theme.pass.opacity(0.5) : c.verdict == "TLE" ? Theme.slow.opacity(0.5) : Theme.fail.opacity(0.5)))
    }

    private func ioBlock(_ k: String, _ text: String) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(k).font(Theme.sans(11)).foregroundStyle(Theme.faint)
            PreBox(text: text, maxHeight: 200)
        }
    }

    // MARK: custom input

    private var customBox: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(j.contest ? "your input (in a contest there is no reference to compare with)" : "your input (the reference solution runs on it too)")
                .font(Theme.sans(11.5)).foregroundStyle(Theme.faint)
            PlainTextArea(text: $j.stdin, placeholder: "stdin", height: 90)
            Button(j.customBusy ? "running…" : "run on this input") { Task { await j.runCustom() } }
                .buttonStyle(Outline()).disabled(j.customBusy)
            if let e = j.customError { Text(e).font(Theme.sans(13)).foregroundStyle(Theme.fail) }
            if let r = j.custom { CustomResultView(r: r) }
        }
        .padding(.vertical, 6)
    }
}

struct CustomResultView: View {
    let r: CustomResult
    var body: some View {
        if r.verdict == "CE" {
            PreBox(text: r.compile ?? "", maxHeight: 400)
        } else {
            let hasRef = r.reference != nil || r.referenceError != nil
            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 10) {
                    VerdictTag(verdict: r.verdict)
                    Chip(text: "\(r.ms ?? 0) ms")
                    if r.matches == true { Text("matches the reference").font(Theme.sans(12)).foregroundStyle(Theme.pass) }
                    else if r.matches == false { Text("differs from the reference").font(Theme.sans(12)).foregroundStyle(Theme.fail) }
                }
                if let m = r.message, !m.isEmpty { Text(m).font(Theme.sans(12.5)).foregroundStyle(Theme.fail) }
                VStack(alignment: .leading, spacing: 3) {
                    Text("your output").font(Theme.sans(11)).foregroundStyle(Theme.faint)
                    PreBox(text: r.stdout ?? "", maxHeight: 220)
                }
                if hasRef {
                    VStack(alignment: .leading, spacing: 3) {
                        Text("reference output").font(Theme.sans(11)).foregroundStyle(Theme.faint)
                        PreBox(text: r.reference ?? r.referenceError ?? "", maxHeight: 220)
                    }
                }
                if let e = r.stderr, !e.isEmpty {
                    VStack(alignment: .leading, spacing: 3) {
                        Text("stderr").font(Theme.sans(11)).foregroundStyle(Theme.faint)
                        PreBox(text: e, maxHeight: 160)
                    }
                }
            }
            .padding(12)
            .overlay(RoundedRectangle(cornerRadius: 8).stroke(Theme.hairline))
        }
    }
}

/// Sample input and output, with a copy button.
struct SamplesView: View {
    let samples: [Sample]
    @Environment(Toast.self) private var toast
    var body: some View {
        ForEach(Array(samples.enumerated()), id: \.offset) { i, s in
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text("sample input \(i + 1)").font(Theme.sans(11)).foregroundStyle(Theme.faint)
                    Spacer()
                    Button("copy") { UIPasteboard.general.string = s.input; toast.show("copied") }.buttonStyle(Bare())
                }
                PreBox(text: s.input, maxHeight: 200)
                Text("sample output \(i + 1)").font(Theme.sans(11)).foregroundStyle(Theme.faint).padding(.top, 4)
                PreBox(text: s.output ?? "", maxHeight: 200)
                if let n = s.note, !n.isEmpty { Prose(blocks: n, color: Theme.muted, size: 13) }
            }
            .padding(.vertical, 8)
        }
    }
}
