import SwiftUI

// The lesson markup, rendered.  Blocks come from cptutor/markup.py; inline markup
// (`code`, **bold**, *emphasis*, 10^9, a_i) is parsed here the way web/app.js does it.

// MARK: - Inline markup

struct InlineStyle {
    var font: Font
    var codeFont: Font
    var color: Color = Theme.ink
    var codeSize: CGFloat
    var isBook = false
}

private struct Pattern {
    let regex: NSRegularExpression
    let kind: Kind
    enum Kind { case bold, em, sup, sub }
}

private let inlinePatterns: [Pattern] = {
    func re(_ p: String) -> NSRegularExpression { try! NSRegularExpression(pattern: p, options: []) }
    return [
        Pattern(regex: re(#"\*\*([^*]+)\*\*"#), kind: .bold),
        Pattern(regex: re(#"(^|[\s(])\*([^*\s][^*]*?)\*(?=[\s).,;:!?]|$)"#), kind: .em),
        Pattern(regex: re(#"([\w)|])\^(\((?:[^()]|\([^()]*\))*\)|\|[^|\s]+\||[-−]?[A-Za-z0-9]+)"#), kind: .sup),
        Pattern(regex: re(#"\b([A-Za-z])_(\([^)]*\)|[A-Za-z0-9]{1,3}\b)"#), kind: .sub),
    ]
}()

private let codeSpan = try! NSRegularExpression(pattern: "`([^`]+)`", options: [])

/// One line of markup as an attributed string.  Code spans are lifted out first, so
/// `a * b` stays code.
func inline(_ text: String, _ style: InlineStyle) -> AttributedString {
    var out = AttributedString()
    let ns = text as NSString
    var last = 0
    for m in codeSpan.matches(in: text, range: NSRange(location: 0, length: ns.length)) {
        if m.range.location > last {
            out.append(styled(ns.substring(with: NSRange(location: last, length: m.range.location - last)), style))
        }
        var code = AttributedString(ns.substring(with: m.range(at: 1)))
        code.font = style.codeFont
        code.foregroundColor = style.color
        code.backgroundColor = Theme.raised
        out.append(code)
        last = m.range.location + m.range.length
    }
    if last < ns.length {
        out.append(styled(ns.substring(from: last), style))
    }
    return out
}

private struct TextStyle {
    var bold = false
    var italic = false
    var script: Int = 0   // +1 sup, -1 sub
}

private func styled(_ text: String, _ style: InlineStyle) -> AttributedString {
    render(text, style, TextStyle())
}

private func render(_ text: String, _ style: InlineStyle, _ ts: TextStyle) -> AttributedString {
    let ns = text as NSString
    var best: (NSTextCheckingResult, Pattern)? = nil
    for p in inlinePatterns {
        if let m = p.regex.firstMatch(in: text, range: NSRange(location: 0, length: ns.length)) {
            if best == nil || m.range.location < best!.0.range.location { best = (m, p) }
        }
    }
    guard let (m, p) = best else { return plain(text, style, ts) }
    var out = AttributedString()
    let prefixEnd: Int
    switch p.kind {
    case .bold:
        prefixEnd = m.range.location
        out.append(plain(ns.substring(to: prefixEnd), style, ts))
        var inner = ts; inner.bold = true
        out.append(render(ns.substring(with: m.range(at: 1)), style, inner))
    case .em:
        // group 1 is the boundary character before the star; keep it
        prefixEnd = m.range.location + m.range(at: 1).length
        out.append(plain(ns.substring(to: prefixEnd), style, ts))
        var inner = ts; inner.italic = true
        out.append(render(ns.substring(with: m.range(at: 2)), style, inner))
    case .sup, .sub:
        // group 1 is the base character; keep it
        prefixEnd = m.range.location + m.range(at: 1).length
        out.append(plain(ns.substring(to: prefixEnd), style, ts))
        var e = ns.substring(with: m.range(at: 2))
        if e.hasPrefix("("), e.hasSuffix(")") { e = String(e.dropFirst().dropLast()) }
        var inner = ts; inner.script = p.kind == .sup ? 1 : -1
        out.append(plain(e, style, inner))
    }
    let tail = m.range.location + m.range.length
    if tail < ns.length {
        out.append(render(ns.substring(from: tail), style, ts))
    }
    return out
}

private func plain(_ text: String, _ style: InlineStyle, _ ts: TextStyle) -> AttributedString {
    var a = AttributedString(text)
    var f = style.font
    if ts.bold { f = f.bold() }
    if ts.italic { f = f.italic() }
    a.font = f
    a.foregroundColor = style.color
    if ts.script != 0 {
        // Smaller and raised or lowered: 10^9 and a_i outside code.
        a.font = scriptFont(style, bold: ts.bold, italic: ts.italic)
        a.baselineOffset = ts.script > 0 ? style.codeSize * 0.42 : -style.codeSize * 0.18
    }
    return a
}

private func scriptFont(_ style: InlineStyle, bold: Bool, italic: Bool) -> Font {
    var f = Theme.sans(style.codeSize * 0.78)
    if let fam = Theme.bookFamily, style.isBook { f = .custom(fam, size: style.codeSize * 0.8) }
    if bold { f = f.bold() }
    if italic { f = f.italic() }
    return f
}

extension InlineStyle {
    static func book(_ size: CGFloat = 17, color: Color = Theme.ink) -> InlineStyle {
        InlineStyle(font: Theme.book(size), codeFont: Theme.mono(size * 0.82), color: color, codeSize: size * 0.82, isBook: true)
    }
    static func sans(_ size: CGFloat = 15, color: Color = Theme.ink, weight: Font.Weight = .regular) -> InlineStyle {
        InlineStyle(font: Theme.sans(size, weight), codeFont: Theme.mono(size * 0.88), color: color, codeSize: size * 0.88)
    }
}

// MARK: - C++ highlighting

private let cppKeywords: Set<String> = Set(("alignas alignof and asm auto bitand bitor break case catch class compl const " +
    "constexpr const_cast continue decltype default delete do dynamic_cast else enum explicit export " +
    "extern false for friend goto if inline mutable namespace new noexcept not nullptr operator or " +
    "private protected public register reinterpret_cast return sizeof static static_assert " +
    "static_cast struct switch template this throw true try typedef typeid typename union using " +
    "virtual volatile while xor").split(separator: " ").map(String.init))

private let cppTypes: Set<String> = Set(("int long short char bool double float void unsigned signed size_t string " +
    "vector pair map set multiset multimap unordered_map unordered_set queue deque stack " +
    "priority_queue array bitset tuple ll ull ld pii pll vi vll greater less int64_t uint64_t " +
    "int32_t uint32_t __int128 stringstream istringstream ostringstream function optional list " +
    "mt19937 mt19937_64 complex").split(separator: " ").map(String.init))

private let cppRegex = try! NSRegularExpression(
    pattern: #"(//[^\n]*|/\*[\s\S]*?(?:\*/|$))|("(?:\\.|[^"\\\n])*"?|'(?:\\.|[^'\\\n])*'?)|(^[ \t]*#[^\n]*)|(\b\d[\w.']*)|([A-Za-z_]\w*)"#,
    options: [.anchorsMatchLines])

func highlightCpp(_ src: String, size: CGFloat = 13) -> AttributedString {
    let font = Theme.mono(size)
    var out = AttributedString()
    let ns = src as NSString
    var last = 0
    func emit(_ s: String, _ color: Color?, italic: Bool = false) {
        guard !s.isEmpty else { return }
        var a = AttributedString(s)
        a.font = italic ? font.italic() : font
        a.foregroundColor = color ?? Theme.ink
        out.append(a)
    }
    for m in cppRegex.matches(in: src, range: NSRange(location: 0, length: ns.length)) {
        if m.range.length == 0 { continue }
        if m.range.location > last {
            emit(ns.substring(with: NSRange(location: last, length: m.range.location - last)), nil)
        }
        let t = ns.substring(with: m.range)
        if m.range(at: 1).location != NSNotFound { emit(t, Theme.codeComment, italic: true) }
        else if m.range(at: 2).location != NSNotFound { emit(t, Theme.codeString) }
        else if m.range(at: 3).location != NSNotFound { emit(t, Theme.codePreproc) }
        else if m.range(at: 4).location != NSNotFound { emit(t, Theme.codeNumber) }
        else if cppKeywords.contains(t) { emit(t, Theme.codeKeyword) }
        else if cppTypes.contains(t) { emit(t, Theme.codeType) }
        else { emit(t, nil) }
        last = m.range.location + m.range.length
    }
    if last < ns.length { emit(ns.substring(from: last), nil) }
    return out
}

// MARK: - Views

/// A code block: highlighted C++ (or verbatim text), scrolling sideways instead of wrapping.
struct CodeBlock: View {
    let text: String
    var lang: String? = "cpp"
    var size: CGFloat = 13

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            Group {
                if lang == nil || lang == "cpp" || lang == "c++" || lang == "" {
                    Text(highlightCpp(text, size: size))
                } else {
                    Text(text).font(Theme.mono(size)).foregroundStyle(Theme.ink)
                }
            }
            .lineSpacing(3)
            .textSelection(.enabled)
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
        }
        .defaultScrollAnchor(.topLeading)
        .background(Theme.raised)
        .overlay(RoundedRectangle(cornerRadius: 7).stroke(Theme.hairline))
        .clipShape(RoundedRectangle(cornerRadius: 7))
    }
}

/// A verbatim box: sample input, program output.
struct PreBox: View {
    let text: String
    var maxHeight: CGFloat? = 260

    var body: some View {
        ScrollView([.horizontal, .vertical], showsIndicators: true) {
            Text(text.isEmpty ? " " : text)
                .font(Theme.mono(12.5))
                .foregroundStyle(Theme.ink)
                .textSelection(.enabled)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.horizontal, 10)
                .padding(.vertical, 8)
        }
        .defaultScrollAnchor(.topLeading)
        .frame(maxHeight: maxHeight)
        .fixedSize(horizontal: false, vertical: true)
        .background(Theme.raised)
        .overlay(RoundedRectangle(cornerRadius: 6).stroke(Theme.hairline))
        .clipShape(RoundedRectangle(cornerRadius: 6))
    }
}

/// Blocks, rendered.  `book` sets the tutor's serif voice; otherwise the system face.
struct Prose: View {
    let blocks: Blocks
    var book = false
    var color: Color = Theme.ink
    var size: CGFloat? = nil

    private var style: InlineStyle {
        book ? .book(size ?? 17, color: color) : .sans(size ?? 15, color: color)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: book ? 11 : 8) {
            ForEach(Array(blocks.enumerated()), id: \.offset) { _, b in
                block(b)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    @ViewBuilder
    private func block(_ b: Block) -> some View {
        switch b.type {
        case "code":
            CodeBlock(text: b.text ?? "", lang: b.lang, size: 12.5)
                .padding(.vertical, 2)
        case "heading":
            Text(inline(b.text ?? "", .sans(14, color: color, weight: .semibold)))
                .padding(.top, 6)
        case "bullet":
            HStack(alignment: .firstTextBaseline, spacing: 8) {
                Text("•").font(style.font).foregroundStyle(Theme.muted)
                Text(inline(b.text ?? "", style)).lineSpacing(lineSpacing)
            }
            .padding(.leading, 6)
        case "num":
            HStack(alignment: .firstTextBaseline, spacing: 8) {
                Text("\(b.n ?? 1).").font(style.font).foregroundStyle(Theme.muted)
                Text(inline(b.text ?? "", style)).lineSpacing(lineSpacing)
            }
            .padding(.leading, 6)
        case "table":
            table(b.rows ?? [])
        default:
            Text(inline(b.text ?? "", style))
                .lineSpacing(lineSpacing)
                .textSelection(.enabled)
        }
    }

    private var lineSpacing: CGFloat { book ? 5 : 3 }

    /// Cells wrap rather than the table scrolling sideways: on a phone the whole row
    /// should be readable at once.
    private func table(_ rows: [[String]]) -> some View {
        Group {
            Grid(alignment: .topLeading, horizontalSpacing: 14, verticalSpacing: 0) {
                ForEach(Array(rows.enumerated()), id: \.offset) { i, cells in
                    GridRow {
                        ForEach(Array(cells.enumerated()), id: \.offset) { _, c in
                            Text(inline(c, i == 0 ? .sans(12.5, color: Theme.muted) : (book ? .book(15, color: color) : .sans(14, color: color))))
                                .padding(.vertical, 5)
                                .fixedSize(horizontal: false, vertical: true)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }
                    Divider().overlay(Theme.hairline)
                }
            }
        }
        .padding(.vertical, 4)
    }
}
