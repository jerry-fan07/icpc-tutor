import SwiftUI

// MARK: - Navigation

enum Route: Hashable {
    case lesson(String)
    case problem(String)
    case contestProblem(String)
    case review
    case lessons
    case problems
    case contest
    case notebook
    case playground
    case stats
    case settings

    /// The web app's hash routes, as the server sends them in today's plan.
    init?(hash: String) {
        var h = hash
        if h.hasPrefix("#") { h.removeFirst() }
        let parts = h.split(separator: "/").map(String.init)
        switch parts.first {
        case "review": self = .review
        case "browse": self = .lessons
        case "problems": self = .problems
        case "lesson" where parts.count > 1: self = .lesson(parts[1])
        case "problem" where parts.count > 1: self = .problem(parts[1])
        case "contest": self = parts.count > 1 ? .contestProblem(parts[1]) : .contest
        case "stats": self = .stats
        case "notebook": self = .notebook
        case "playground": self = .playground
        case "about", "settings": self = .settings
        default: return nil
        }
    }
}

struct RouteDestination: View {
    let route: Route
    var body: some View {
        switch route {
        case .lesson(let id): LessonScreen(id: id)
        case .problem(let ref): ProblemScreen(ref: ref)
        case .contestProblem(let letter): ContestProblemScreen(letter: letter)
        case .review: ReviewScreen()
        case .lessons: LessonsScreen()
        case .problems: ProblemsScreen()
        case .contest: ContestScreen()
        case .notebook: NotebookScreen()
        case .playground: PlaygroundScreen()
        case .stats: StatsScreen()
        case .settings: SettingsScreen()
        }
    }
}

// MARK: - Toast

@Observable
final class Toast {
    var message: String? = nil
    private var token = 0

    func show(_ msg: String) {
        token += 1
        let mine = token
        withAnimation(.easeOut(duration: 0.2)) { message = msg }
        Task { @MainActor in
            try? await Task.sleep(for: .seconds(2.8))
            if mine == token { withAnimation { message = nil } }
        }
    }
}

struct ToastOverlay: View {
    @Environment(Toast.self) private var toast
    var body: some View {
        VStack {
            Spacer()
            if let m = toast.message {
                Text(m)
                    .font(Theme.sans(13))
                    .foregroundStyle(Theme.paper)
                    .padding(.horizontal, 14).padding(.vertical, 9)
                    .background(Theme.ink.opacity(0.92))
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                    .padding(.bottom, 70)
                    .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
        .allowsHitTesting(false)
    }
}

// MARK: - Loading

/// Loads a value, shows a spinner, an error with retry, or the content; pull to refresh.
struct Loader<T, Content: View>: View {
    let load: () async throws -> T
    @ViewBuilder let content: (T, _ reload: @escaping () async -> Void) -> Content

    @State private var value: T? = nil
    @State private var error: String? = nil
    @State private var generation = 0

    var body: some View {
        Group {
            if let v = value {
                content(v, reload)
            } else if let e = error {
                ErrorView(message: e) { await reload() }
            } else {
                ProgressView().tint(Theme.muted)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
        .task(id: generation) { await reload() }
        .refreshable { await reload() }
    }

    func reload() async {
        do {
            let v = try await load()
            await MainActor.run { value = v; error = nil }
        } catch {
            await MainActor.run { if value == nil { self.error = error.localizedDescription } }
        }
    }
}

struct ErrorView: View {
    let message: String
    let retry: () async -> Void
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("something went wrong").font(Theme.sans(22)).foregroundStyle(Theme.ink)
            Text(message).font(Theme.sans(14)).foregroundStyle(Theme.fail)
            Text("Is the server running on the Mac?  Start it with  python3 cp.py serve --host 0.0.0.0  and check the address under More › Settings.")
                .font(Theme.sans(13)).foregroundStyle(Theme.muted)
            HStack {
                Button("try again") { Task { await retry() } }.buttonStyle(Outline())
                NavigationLink(value: Route.settings) { Text("settings") }.buttonStyle(Outline())
            }
        }
        .padding(20)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .background(Theme.paper)
    }
}

// MARK: - Buttons

struct Prominent: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(Theme.sans(14, .medium))
            .foregroundStyle(Theme.onAccent)
            .padding(.horizontal, 15).padding(.vertical, 8)
            .background(Theme.accent)
            .clipShape(RoundedRectangle(cornerRadius: 7))
            .opacity(configuration.isPressed ? 0.8 : 1)
    }
}

struct Outline: ButtonStyle {
    var color: Color = Theme.ink
    var border: Color = Theme.hairline
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(Theme.sans(14))
            .foregroundStyle(configuration.isPressed ? Theme.accent : color)
            .padding(.horizontal, 13).padding(.vertical, 7)
            .background(Theme.paper)
            .overlay(RoundedRectangle(cornerRadius: 7).stroke(configuration.isPressed ? Theme.accent : border))
    }
}

struct Bare: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(Theme.sans(13))
            .foregroundStyle(configuration.isPressed ? Theme.accent : Theme.muted)
    }
}

/// A destructive action asks for a second tap within three seconds, like the web app.
@Observable
final class Armed {
    var what = ""
    var at = Date.distantPast
    func twice(_ what: String, _ toast: Toast, _ msg: String) -> Bool {
        if self.what == what && Date().timeIntervalSince(at) < 3 {
            self.what = ""
            return true
        }
        self.what = what
        at = Date()
        toast.show(msg)
        return false
    }
}

// MARK: - Small pieces

struct SectionHeading: View {
    let title: String
    var value: String? = nil
    var rule = true
    var body: some View {
        VStack(spacing: 6) {
            HStack(alignment: .firstTextBaseline) {
                Text(title).font(Theme.sans(13)).foregroundStyle(Theme.muted)
                Spacer()
                if let v = value, !v.isEmpty {
                    Text(v).font(Theme.sans(12)).foregroundStyle(Theme.faint)
                }
            }
            if rule { Rectangle().fill(Theme.hairline).frame(height: 1) }
        }
        .padding(.top, 24)
        .padding(.bottom, 6)
    }
}

struct TitleLine: View {
    let title: String
    var note: String? = nil
    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(title).font(Theme.sans(26)).foregroundStyle(Theme.ink)
            if let n = note, !n.isEmpty {
                Text(n).font(Theme.sans(12)).foregroundStyle(Theme.faint)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

struct Figure: View {
    let n: String
    let k: String
    var body: some View {
        VStack(alignment: .leading, spacing: 1) {
            Text(n).font(Theme.sans(24)).monospacedDigit().foregroundStyle(Theme.ink)
            Text(k).font(Theme.sans(12)).foregroundStyle(Theme.faint)
        }
    }
}

struct Bar: View {
    let fraction: Double
    var color: Color = Theme.accent
    var body: some View {
        GeometryReader { g in
            ZStack(alignment: .leading) {
                Capsule().fill(Theme.hairline)
                Capsule().fill(color).frame(width: g.size.width * min(1, max(0, fraction)))
            }
        }
        .frame(height: 4)
    }
}

struct Meter: View {
    let label: String
    let pct: Int
    var body: some View {
        HStack(spacing: 10) {
            Text(label).font(Theme.sans(13)).foregroundStyle(Theme.ink).lineLimit(1)
            Spacer(minLength: 8)
            Bar(fraction: Double(pct) / 100, color: pct >= 80 ? Theme.pass : pct >= 65 ? Theme.accent : Theme.fail)
                .frame(width: 70)
            Text("\(pct)").font(Theme.mono(11)).foregroundStyle(Theme.faint).frame(width: 28, alignment: .trailing)
        }
        .padding(.vertical, 4)
    }
}

struct ForecastStrip: View {
    let counts: [Int]
    var body: some View {
        let peak = max(1, counts.dropFirst().max() ?? 1)
        HStack(alignment: .bottom, spacing: 3) {
            ForEach(Array(counts.enumerated()), id: \.offset) { i, n in
                RoundedRectangle(cornerRadius: 2)
                    .fill(n > 0 ? Theme.accent.opacity(0.35 + 0.65 * min(1, Double(n) / Double(peak))) : Theme.hairline)
                    .frame(height: 22)
                    .overlay(RoundedRectangle(cornerRadius: 2).stroke(i == 0 ? Theme.accent : .clear))
            }
        }
    }
}

struct StatusDot: View {
    let status: String   // new | started | learned | ahead
    var body: some View {
        Circle()
            .fill(status == "started" ? Theme.accent : status == "learned" ? Theme.pass : .clear)
            .overlay(Circle().stroke(Theme.faint, lineWidth: status == "new" || status == "ahead" ? 1 : 0))
            .frame(width: 7, height: 7)
            .opacity(status == "ahead" ? 0.4 : 1)
    }
}

struct VerdictTag: View {
    let verdict: String
    var body: some View {
        Text(verdict)
            .font(Theme.mono(11).weight(.semibold))
            .foregroundStyle(Theme.verdictColor(verdict))
            .frame(minWidth: 30, alignment: .leading)
    }
}

/// A balloon per problem: outlined until solved, filled after, like the ones on the
/// tables at a contest.
struct Balloon: View {
    let color: String
    let solved: Bool
    var size: CGFloat = 10

    var body: some View {
        let c = Color(hex: color)
        BalloonShape()
            .fill(solved ? c : .clear)
            .overlay(BalloonShape().stroke(c, lineWidth: solved ? 0 : 1.3))
            .overlay(alignment: .topLeading) {
                if solved {
                    Ellipse().fill(.white.opacity(0.35))
                        .frame(width: size * 0.16, height: size * 0.26)
                        .offset(x: size * 0.27, y: size * 0.2)
                }
            }
            .frame(width: size, height: size * 1.25)
    }
}

struct BalloonShape: Shape {
    func path(in rect: CGRect) -> Path {
        // the SVG path from app.js, in a 20 x 25 box
        let sx = rect.width / 20, sy = rect.height / 25
        func p(_ x: CGFloat, _ y: CGFloat) -> CGPoint { CGPoint(x: rect.minX + x * sx, y: rect.minY + y * sy) }
        var path = Path()
        path.move(to: p(10, 1.2))
        path.addCurve(to: p(2, 9.3), control1: p(5.1, 1.2), control2: p(2, 5))
        path.addCurve(to: p(9, 19.4), control1: p(2, 14.2), control2: p(6.2, 18.4))
        path.addLine(to: p(7.9, 21))
        path.addLine(to: p(12.1, 21))
        path.addLine(to: p(11, 19.4))
        path.addCurve(to: p(18, 9.3), control1: p(13.8, 18.4), control2: p(18, 14.2))
        path.addCurve(to: p(10, 1.2), control1: p(18, 5), control2: p(14.9, 1.2))
        path.closeSubpath()
        return path
    }
}

struct BalloonRow: View {
    let balloons: [BalloonRef]
    var body: some View {
        HStack(spacing: 3) {
            ForEach(balloons, id: \.ref) { Balloon(color: $0.color, solved: $0.solved, size: 9) }
        }
    }
}

/// A balloon that floats up after an AC.
struct FloatingBalloon: View {
    let color: String
    @State private var up = false
    var body: some View {
        Balloon(color: color, solved: true, size: 34)
            .offset(y: up ? -700 : 0)
            .opacity(up ? 0 : 1)
            .onAppear { withAnimation(.easeIn(duration: 3.2)) { up = true } }
            .allowsHitTesting(false)
    }
}

/// A row in a list: like `.rowbtn` on the web.
struct Row<Content: View>: View {
    @ViewBuilder let content: () -> Content
    var body: some View {
        HStack(spacing: 11) { content() }
            .padding(.horizontal, 10).padding(.vertical, 9)
            .frame(maxWidth: .infinity, alignment: .leading)
            .contentShape(Rectangle())
    }
}

struct RowLink<Content: View>: View {
    let route: Route
    @ViewBuilder let content: () -> Content
    var body: some View {
        NavigationLink(value: route) { Row(content: content) }
            .buttonStyle(RowPress())
    }
}

struct RowPress: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .background(configuration.isPressed ? Theme.raised : .clear)
            .clipShape(RoundedRectangle(cornerRadius: 7))
    }
}

struct Tabs: View {
    let options: [(String, String)]
    @Binding var selected: String
    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 6) {
                ForEach(options, id: \.0) { k, label in
                    Button(label) { selected = k }
                        .buttonStyle(Outline(color: selected == k ? Theme.accent : Theme.muted,
                                             border: selected == k ? Theme.accent : Theme.hairline))
                }
            }
        }
    }
}

struct Chip: View {
    let text: String
    var color: Color = Theme.faint
    var body: some View {
        Text(text).font(Theme.sans(12)).foregroundStyle(color)
    }
}

// MARK: - Screen scaffolding

struct Screen<Content: View>: View {
    @ViewBuilder let content: () -> Content
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) { content() }
                .padding(.horizontal, 18)
                .padding(.top, 8)
                .padding(.bottom, 60)
                .frame(maxWidth: 720)
                .frame(maxWidth: .infinity)
        }
        .background(Theme.paper)
        .scrollDismissesKeyboard(.interactively)
    }
}

/// Time on task: one heartbeat a minute while a working screen is open.  Stacked
/// screens (a lesson under a problem) share one clock, so a minute is never counted twice.
struct Heartbeat: ViewModifier {
    @Environment(\.scenePhase) private var phase
    nonisolated(unsafe) static var lastSent = Date.distantPast
    func body(content: Content) -> some View {
        content.task {
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(60))
                guard phase == .active, Date().timeIntervalSince(Heartbeat.lastSent) > 55 else { continue }
                Heartbeat.lastSent = Date()
                try? await API.shared.post("heartbeat", ["seconds": 60])
            }
        }
    }
}

extension View {
    func heartbeat() -> some View { modifier(Heartbeat()) }
}
