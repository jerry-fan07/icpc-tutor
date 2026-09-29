import SwiftUI

@main
struct ICPCTutorApp: App {
    @State private var toast = Toast()
    @State private var armed = Armed()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(toast)
                .environment(armed)
                .tint(Theme.accent)
        }
    }
}

struct RootView: View {
    var body: some View {
        TabView {
            Tab("today", systemImage: "sun.max") { Stack(initial: launchRoute) { TodayScreen() } }
            Tab("lessons", systemImage: "book") { Stack { LessonsScreen() } }
            Tab("problems", systemImage: "balloon") { Stack { ProblemsScreen() } }
            Tab("review", systemImage: "arrow.trianglehead.2.clockwise.rotate.90") { Stack { ReviewScreen() } }
            Tab("more", systemImage: "ellipsis") { Stack { MoreScreen() } }
        }
        .overlay { ToastOverlay() }
    }
}

/// `-route "#/lesson/algo01"` on the command line opens that screen at launch (for
/// screenshots and testing in the simulator).
private let launchRoute: Route? = {
    let args = ProcessInfo.processInfo.arguments
    guard let i = args.firstIndex(of: "-route"), i + 1 < args.count else { return nil }
    return Route(hash: args[i + 1])
}()

/// One navigation stack per tab; every screen pushes `Route`s.
struct Stack<Content: View>: View {
    var initial: Route? = nil
    @ViewBuilder let content: () -> Content
    @State private var path = NavigationPath()
    var body: some View {
        NavigationStack(path: $path) {
            content()
                .onAppear { if let r = initial, path.isEmpty { path.append(r) } }
                .navigationDestination(for: Route.self) { RouteDestination(route: $0) }
                .toolbarBackground(Theme.paper, for: .navigationBar)
        }
    }
}

struct MoreScreen: View {
    var body: some View {
        Screen {
            TitleLine(title: "more")
            VStack(spacing: 0) {
                moreRow(.contest, "contest", "a virtual contest against the clock", "flag.checkered")
                moreRow(.notebook, "notebook", "the code of everything you have solved", "text.book.closed")
                moreRow(.playground, "playground", "compile and run any C++", "terminal")
                moreRow(.stats, "stats", "solved, verdicts, streak, retention", "chart.bar")
                moreRow(.settings, "settings", "server address, about", "gearshape")
            }
            .padding(.top, 14)
        }
        .navigationTitle("more")
        .navigationBarTitleDisplayMode(.inline)
    }

    private func moreRow(_ r: Route, _ title: String, _ sub: String, _ icon: String) -> some View {
        RowLink(route: r) {
            Image(systemName: icon).foregroundStyle(Theme.accent).frame(width: 22)
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(Theme.sans(15)).foregroundStyle(Theme.ink)
                Text(sub).font(Theme.sans(12)).foregroundStyle(Theme.faint)
            }
            Spacer()
            Image(systemName: "chevron.right").font(.system(size: 12)).foregroundStyle(Theme.faint)
        }
    }
}
