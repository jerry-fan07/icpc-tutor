import SwiftUI

private let playDefault = """
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long long> a(n);
    for (auto& x : a) cin >> x;
    sort(a.begin(), a.end());
    for (auto x : a) cout << x << ' ';
    cout << '\\n';
    return 0;
}

"""

struct PlaygroundScreen: View {
    @AppStorage("cp.play.code") private var code = playDefault
    @AppStorage("cp.play.in") private var stdin = "5\n3 1 4 1 5\n"
    @State private var result: CustomResult? = nil
    @State private var error: String? = nil
    @State private var busy = false
    @State private var startedAt: Date? = nil
    @Environment(Toast.self) private var toast
    @Environment(Armed.self) private var armed

    var body: some View {
        Screen {
            TitleLine(title: "playground", note: "compile and run anything")
            EditorBox(text: $code, height: 360).padding(.top, 14)
            HStack {
                Button(busy ? "running…" : "run") { Task { await run() } }.buttonStyle(Prominent()).disabled(busy)
                Button("reset") {
                    guard armed.twice("play", toast, "Tap again to restore the example program.") else { return }
                    code = playDefault
                }.buttonStyle(Bare())
                Spacer()
            }
            .padding(.top, 10)
            SectionHeading(title: "stdin", rule: false)
            PlainTextArea(text: $stdin, placeholder: "input", height: 100)
            Group {
                if let t0 = startedAt {
                    TimelineView(.periodic(from: t0, by: 0.1)) { ctx in
                        Text(String(format: "compiling and running… %.1f s", ctx.date.timeIntervalSince(t0)))
                            .font(Theme.sans(12.5)).foregroundStyle(Theme.faint)
                    }
                } else if let e = error {
                    Text(e).font(Theme.sans(13)).foregroundStyle(Theme.fail)
                } else if let r = result {
                    if r.verdict == "CE" {
                        Text("Compilation Error").font(Theme.sans(17, .medium)).foregroundStyle(Theme.fail)
                        PreBox(text: r.compile ?? "", maxHeight: 400).padding(.top, 6)
                    } else {
                        HStack(alignment: .firstTextBaseline, spacing: 10) {
                            Text(r.verdict == "AC" ? "ran" : (verdictName[r.verdict] ?? r.verdict))
                                .font(Theme.sans(17, .medium)).foregroundStyle(r.verdict == "AC" ? Theme.ink : Theme.verdictColor(r.verdict))
                            Text("\(r.ms ?? 0) ms · \(String(format: "%.1f", Double(r.kb ?? 0) / 1024)) MB" + ((r.message ?? "").isEmpty ? "" : " · \(r.message!)"))
                                .font(Theme.sans(12)).foregroundStyle(Theme.muted)
                        }
                        Text("stdout").font(Theme.sans(11)).foregroundStyle(Theme.faint).padding(.top, 8)
                        PreBox(text: r.stdout ?? "", maxHeight: 300)
                        if let e = r.stderr, !e.isEmpty {
                            Text("stderr").font(Theme.sans(11)).foregroundStyle(Theme.faint).padding(.top, 8)
                            PreBox(text: e, maxHeight: 200)
                        }
                        if let w = r.warnings, !w.isEmpty {
                            DisclosureGroup { PreBox(text: w, maxHeight: 300) } label: {
                                Text("warnings").font(Theme.sans(12.5)).foregroundStyle(Theme.muted)
                            }
                            .tint(Theme.muted).padding(.top, 8)
                        }
                    }
                }
            }
            .padding(.top, 14)
        }
        .heartbeat()
        .navigationTitle("playground")
        .navigationBarTitleDisplayMode(.inline)
    }

    private func run() async {
        busy = true
        startedAt = Date()
        result = nil
        error = nil
        defer { busy = false; startedAt = nil }
        do {
            result = try await API.shared.post("playground", ["code": code, "input": stdin], timeout: 240)
        } catch {
            self.error = error.localizedDescription
        }
    }
}
