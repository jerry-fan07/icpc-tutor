import Foundation

/// The JSON API of cptutor/server.py.  Reads are GET with a query string; anything that
/// changes progress is a POST with a JSON body.  Every reply is `{ok, data}` or `{ok, error}`.
final class API: @unchecked Sendable {
    static let shared = API()

    static let defaultURL = "http://Jerrys-MacBook-Pro-7616.local:8000"
    static let urlKey = "serverURL"

    struct Failure: LocalizedError {
        let message: String
        let status: Int
        var errorDescription: String? { message }
    }

    /// Ops the server accepts as GET (server.py READS).
    private static let reads: Set<String> = ["today", "lessons", "lesson", "problem", "problems", "due",
                                             "stats", "env", "ping", "contest", "notebook"]

    var baseURL: URL {
        let s = UserDefaults.standard.string(forKey: API.urlKey) ?? API.defaultURL
        return URL(string: s.trimmingCharacters(in: .whitespacesAndNewlines)) ?? URL(string: API.defaultURL)!
    }

    private let session: URLSession = {
        let c = URLSessionConfiguration.default
        c.timeoutIntervalForRequest = 30
        c.waitsForConnectivity = false
        return URLSession(configuration: c)
    }()

    private let decoder: JSONDecoder = {
        let d = JSONDecoder()
        d.keyDecodingStrategy = .convertFromSnakeCase
        return d
    }()

    private struct Envelope<T: Decodable>: Decodable {
        let ok: Bool
        let data: T?
        let error: String?
    }

    func get<T: Decodable>(_ op: String, _ args: [String: String] = [:]) async throws -> T {
        precondition(API.reads.contains(op), "\(op) needs POST")
        var comps = URLComponents(url: baseURL.appendingPathComponent("api/\(op)"), resolvingAgainstBaseURL: false)!
        if !args.isEmpty {
            comps.queryItems = args.map { URLQueryItem(name: $0.key, value: $0.value) }
        }
        var req = URLRequest(url: comps.url!)
        req.httpMethod = "GET"
        return try await perform(req, op: op)
    }

    func post<T: Decodable>(_ op: String, _ args: [String: Any] = [:], timeout: TimeInterval = 30) async throws -> T {
        var req = URLRequest(url: baseURL.appendingPathComponent("api/\(op)"))
        req.httpMethod = "POST"
        req.timeoutInterval = timeout
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONSerialization.data(withJSONObject: args, options: [])
        return try await perform(req, op: op)
    }

    /// A POST whose reply is not needed.
    func post(_ op: String, _ args: [String: Any] = [:]) async throws {
        let _: Empty = try await post(op, args)
    }

    struct Empty: Decodable {}

    private func perform<T: Decodable>(_ req: URLRequest, op: String) async throws -> T {
        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(for: req)
        } catch {
            throw Failure(message: "Cannot reach \(baseURL.host ?? "the server"): \(error.localizedDescription)", status: 0)
        }
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0
        let env: Envelope<T>
        do {
            env = try decoder.decode(Envelope<T>.self, from: data)
        } catch let e as DecodingError {
            // A response we could not read: say which field, so the app can be fixed.
            if let raw = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               raw["ok"] as? Bool == false, let msg = raw["error"] as? String {
                throw Failure(message: msg, status: status)
            }
            throw Failure(message: "\(op): \(describe(e))", status: status)
        }
        if !env.ok || status >= 400 {
            throw Failure(message: env.error ?? "request failed (\(status))", status: status)
        }
        guard let d = env.data else { throw Failure(message: "\(op): empty reply", status: status) }
        return d
    }

    private func describe(_ e: DecodingError) -> String {
        switch e {
        case .keyNotFound(let k, let c): return "missing \(path(c) + k.stringValue)"
        case .typeMismatch(let t, let c): return "\(path(c)) is not \(t)"
        case .valueNotFound(let t, let c): return "\(path(c)) is null, expected \(t)"
        case .dataCorrupted(let c): return "bad data at \(path(c))"
        @unknown default: return "unreadable reply"
        }
    }

    private func path(_ c: DecodingError.Context) -> String {
        c.codingPath.map { $0.intValue.map { "[\($0)]" } ?? $0.stringValue }.joined(separator: ".")
    }
}
