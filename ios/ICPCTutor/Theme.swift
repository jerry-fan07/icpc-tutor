import SwiftUI
import UIKit

// The web app's warm paper and hairlines, with ICPC blue as the one accent.  Every
// colour has a light and a dark value, taken from web/style.css.
enum Theme {
    private static func dyn(_ light: UInt32, _ dark: UInt32) -> Color {
        Color(UIColor { traits in
            UIColor(hex: traits.userInterfaceStyle == .dark ? dark : light)
        })
    }

    static let paper = dyn(0xFBFAF7, 0x131417)
    static let raised = dyn(0xF2F0EA, 0x1B1C20)
    static let sunk = dyn(0xECE9E1, 0x202127)
    static let ink = dyn(0x18181B, 0xEFEEEA)
    static let muted = dyn(0x66655F, 0x9B9A94)
    static let faint = dyn(0xA09E96, 0x67665F)
    static let hairline = dyn(0xE2DFD6, 0x2A2B31)
    static let accent = dyn(0x2456C8, 0x82A7FF)
    static let accentSoft = dyn(0xE7EDFA, 0x1B2438)
    static let onAccent = dyn(0xFFFFFF, 0x0F1115)
    static let pass = dyn(0x2B6B47, 0x6FCF97)
    static let passSoft = dyn(0xE4F1E8, 0x16261D)
    static let fail = dyn(0xAE3A2C, 0xF08A78)
    static let failSoft = dyn(0xF8E6E2, 0x2C1916)
    static let slow = dyn(0x9A6A12, 0xE6B955)
    static let slowSoft = dyn(0xF7EDD9, 0x2A2314)

    static let codeKeyword = dyn(0x8A3FB8, 0xC792EA)
    static let codeType = dyn(0x1F6FB2, 0x82AAFF)
    static let codeString = dyn(0x2B7A3D, 0xA5D6A7)
    static let codeNumber = dyn(0xB35C12, 0xF5A26B)
    static let codeComment = dyn(0x9A988F, 0x6B6A64)
    static let codePreproc = dyn(0xB0306A, 0xF07CB0)

    /// The book face for the tutor's voice.  Iowan Old Style ships with iOS; fall back to
    /// the system serif if it is ever missing.
    static let bookFamily: String? = {
        let wanted = ["Iowan Old Style", "Charter", "Palatino"]
        let families = Set(UIFont.familyNames)
        return wanted.first { families.contains($0) }
    }()

    static func book(_ size: CGFloat) -> Font {
        if let f = bookFamily { return .custom(f, size: size) }
        return .system(size: size, design: .serif)
    }

    static func mono(_ size: CGFloat) -> Font {
        .system(size: size, design: .monospaced)
    }

    static func sans(_ size: CGFloat, _ weight: Font.Weight = .regular) -> Font {
        .system(size: size, weight: weight)
    }

    static func verdictColor(_ v: String) -> Color {
        switch v {
        case "AC": return pass
        case "TLE": return slow
        case "CE": return muted
        default: return fail
        }
    }

    static func verdictSoft(_ v: String) -> Color {
        switch v {
        case "AC": return passSoft
        case "TLE": return slowSoft
        case "CE": return raised
        default: return failSoft
        }
    }
}

extension UIColor {
    convenience init(hex: UInt32) {
        self.init(red: CGFloat((hex >> 16) & 0xFF) / 255,
                  green: CGFloat((hex >> 8) & 0xFF) / 255,
                  blue: CGFloat(hex & 0xFF) / 255, alpha: 1)
    }
}

extension Color {
    init(hex: String) {
        var s = hex.trimmingCharacters(in: .whitespaces)
        if s.hasPrefix("#") { s.removeFirst() }
        var v: UInt64 = 0
        Scanner(string: s).scanHexInt64(&v)
        self.init(UIColor(hex: UInt32(v & 0xFFFFFF)))
    }
}

let verdictName: [String: String] = [
    "AC": "Accepted", "WA": "Wrong Answer", "TLE": "Time Limit Exceeded",
    "RE": "Run-Time Error", "OLE": "Output Limit Exceeded", "CE": "Compilation Error",
]

func plural(_ n: Int, _ word: String) -> String {
    "\(n) \(word)\(n == 1 ? "" : "s")"
}

private let months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

func shortDate(_ iso: String?) -> String {
    guard let iso, iso.count >= 10 else { return iso ?? "" }
    let parts = iso.prefix(10).split(separator: "-")
    guard parts.count == 3, let m = Int(parts[1]), let d = Int(parts[2]), (1...12).contains(m) else { return iso }
    return "\(months[m - 1]) \(d)"
}

func whenAgo(_ iso: String?) -> String {
    guard let iso else { return "" }
    let f = ISO8601DateFormatter()
    f.formatOptions = [.withInternetDateTime]
    f.timeZone = .current
    var date = f.date(from: iso)
    if date == nil {
        let df = DateFormatter()
        df.dateFormat = "yyyy-MM-dd'T'HH:mm:ss"
        df.timeZone = .current
        date = df.date(from: String(iso.prefix(19)))
    }
    guard let date else { return shortDate(iso) }
    let s = Date().timeIntervalSince(date)
    if s < 60 { return "just now" }
    if s < 3600 { return "\(Int((s / 60).rounded())) min ago" }
    if s < 86400 { return "\(Int((s / 3600).rounded())) h ago" }
    return shortDate(iso)
}

func clock(_ seconds: Int) -> String {
    let s = max(0, seconds)
    return String(format: "%d:%02d:%02d", s / 3600, s % 3600 / 60, s % 60)
}
