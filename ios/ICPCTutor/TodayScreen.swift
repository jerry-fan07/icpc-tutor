import SwiftUI

struct TodayScreen: View {
    var body: some View {
        Loader(load: { try await API.shared.get("today") as Today }) { t, _ in
            Screen {
                let date = Date().formatted(.dateTime.weekday(.abbreviated).month(.abbreviated).day())
                TitleLine(title: "today",
                          note: [date, "day \(t.day)", t.streak > 0 ? "streak \(t.streak)d" : ""].filter { !$0.isEmpty }.joined(separator: " · "))

                ForEach(t.warnings ?? [], id: \.self) { w in
                    WarnBox(text: w)
                }

                HStack(spacing: 12) {
                    Bar(fraction: Double(t.minutes) / Double(max(1, t.target)))
                    Text("\(t.minutes) of \(t.target) min today").font(Theme.sans(12)).foregroundStyle(Theme.muted).fixedSize()
                }
                .padding(.top, 16)

                VStack(spacing: 0) {
                    ForEach(t.plan) { r in planRow(r) }
                }
                .padding(.top, 8)
                .padding(.horizontal, -10)

                SectionHeading(title: "next lessons", value: "\(t.learned) of \(t.lessons) learned")
                VStack(spacing: 0) {
                    ForEach(t.upcoming) { u in upcomingRow(u) }
                }
                .padding(.horizontal, -10)

                SectionHeading(title: "solved", value: "\(t.solved) / \(t.problems)", rule: false)
                Bar(fraction: Double(t.solved) / Double(max(1, t.problems)))

                SectionHeading(title: "due · next 14 days", value: "\(t.forecast.reduce(0, +))", rule: false)
                ForecastStrip(counts: t.forecast)

                if !t.recent.isEmpty {
                    SectionHeading(title: "recent submissions")
                    VStack(spacing: 0) {
                        ForEach(t.recent) { s in
                            RowLink(route: .problem(s.ref)) {
                                VerdictTag(verdict: s.verdict)
                                Text(s.title).font(Theme.sans(13)).foregroundStyle(Theme.ink).lineLimit(1)
                                Spacer()
                                Chip(text: whenAgo(s.ts))
                            }
                        }
                    }
                    .padding(.horizontal, -10)
                }

                if !t.retention.isEmpty {
                    SectionHeading(title: "retention by lesson")
                    ForEach(t.retention) { Meter(label: $0.label, pct: $0.pct) }
                }
            }
        }
        .navigationTitle("today")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar { ToolbarItem(placement: .principal) { Brand() } }
    }

    @ViewBuilder
    private func planRow(_ r: PlanRow) -> some View {
        let done = r.state == "done"
        let active = r.state == "active"
        let inner = Row {
            Text(r.key)
                .font(Theme.sans(11)).foregroundStyle(active ? Theme.onAccent : Theme.muted)
                .frame(width: 19, height: 19)
                .background(active ? Theme.accent : Theme.raised)
                .clipShape(RoundedRectangle(cornerRadius: 4))
            Text(r.title).font(Theme.sans(14)).foregroundStyle(done ? Theme.faint : Theme.ink)
                .strikethrough(done, color: Theme.faint)
                .frame(width: 64, alignment: .leading)
            Text(r.detail).font(Theme.sans(12.5)).foregroundStyle(done ? Theme.faint : Theme.muted).lineLimit(2)
            Spacer(minLength: 6)
            Text(done ? "✓" : "~\(r.minutes) min").font(Theme.sans(12)).foregroundStyle(done ? Theme.pass : Theme.faint).fixedSize()
        }
        .background(active ? Theme.raised : .clear)
        .clipShape(RoundedRectangle(cornerRadius: 7))
        if let route = Route(hash: r.route) {
            NavigationLink(value: route) { inner }.buttonStyle(RowPress())
        } else {
            inner
        }
    }

    private func upcomingRow(_ u: LessonRow) -> some View {
        let state = u.state ?? u.status ?? "new"
        return RowLink(route: .lesson(u.id)) {
            StatusDot(status: state)
            Text(u.id).font(Theme.mono(11.5)).foregroundStyle(Theme.faint).frame(width: 44, alignment: .leading)
            VStack(alignment: .leading, spacing: 2) {
                Text(u.title).font(Theme.sans(14)).foregroundStyle(state == "ahead" ? Theme.muted : Theme.ink).lineLimit(1)
                if state == "ahead", let m = u.missing, !m.isEmpty {
                    Text("after " + m.prefix(2).joined(separator: ", ")).font(Theme.sans(11.5)).foregroundStyle(Theme.faint)
                }
            }
            Spacer(minLength: 4)
            BalloonRow(balloons: u.balloons ?? [])
            Text(state == "started" ? "\(u.answered ?? 0)/\(u.questions ?? 0) asked" : "~\(u.minutes ?? 0) min")
                .font(Theme.sans(12)).foregroundStyle(Theme.faint).fixedSize()
        }
    }
}

struct Brand: View {
    var body: some View {
        HStack(spacing: 3) {
            Text("icpc").font(Theme.sans(14)).foregroundStyle(Theme.ink)
            Text("tutor").font(Theme.sans(14, .semibold)).foregroundStyle(Theme.accent)
        }
    }
}

struct WarnBox: View {
    let text: String
    var body: some View {
        Text(text)
            .font(Theme.sans(13)).foregroundStyle(Theme.slow)
            .padding(10)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Theme.slowSoft)
            .clipShape(RoundedRectangle(cornerRadius: 7))
            .padding(.top, 12)
    }
}
