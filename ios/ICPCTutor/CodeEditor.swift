import SwiftUI
import UIKit

/// A C++ editor on a phone.  A UITextView with everything a phone keyboard does to
/// code switched off (smart quotes would turn every " into “ and every submission into a
/// CE), a monospaced face, and a key row above the keyboard for the characters C++
/// needs that the letters keyboard hides.
struct CodeEditor: UIViewRepresentable {
    @Binding var text: String
    var minHeight: CGFloat = 320

    func makeUIView(context: Context) -> UITextView {
        let tv = UITextView()
        tv.delegate = context.coordinator
        tv.font = UIFont.monospacedSystemFont(ofSize: 13, weight: .regular)
        tv.backgroundColor = .clear
        tv.textColor = UIColor(Theme.ink)
        tv.autocorrectionType = .no
        tv.autocapitalizationType = .none
        tv.smartQuotesType = .no
        tv.smartDashesType = .no
        tv.smartInsertDeleteType = .no
        tv.spellCheckingType = .no
        tv.keyboardType = .asciiCapable
        tv.returnKeyType = .default
        tv.textContainerInset = UIEdgeInsets(top: 12, left: 10, bottom: 12, right: 10)
        tv.isScrollEnabled = true
        tv.alwaysBounceVertical = true
        tv.textContainer.lineBreakMode = .byClipping
        tv.textContainer.widthTracksTextView = false
        tv.textContainer.size = CGSize(width: 4000, height: CGFloat.greatestFiniteMagnitude)
        tv.showsHorizontalScrollIndicator = true
        tv.inputAccessoryView = context.coordinator.keyRow(for: tv)
        tv.text = text
        return tv
    }

    func updateUIView(_ tv: UITextView, context: Context) {
        if tv.text != text {
            let sel = tv.selectedRange
            tv.text = text
            tv.selectedRange = NSRange(location: min(sel.location, (text as NSString).length), length: 0)
        }
        // keep lines from wrapping: the container is wide, the view scrolls sideways
        tv.contentSize = CGSize(width: max(tv.bounds.width, tv.contentSize.width), height: tv.contentSize.height)
    }

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    final class Coordinator: NSObject, UITextViewDelegate {
        var parent: CodeEditor
        init(_ p: CodeEditor) { parent = p }

        func textViewDidChange(_ tv: UITextView) {
            parent.text = tv.text
        }

        // Auto-indent on return; a closing brace outdents; Tab inserts four spaces.
        func textView(_ tv: UITextView, shouldChangeTextIn range: NSRange, replacementText s: String) -> Bool {
            let ns = tv.text as NSString
            if s == "\n" {
                let lineStart = ns.range(of: "\n", options: .backwards, range: NSRange(location: 0, length: range.location)).location
                let ls = lineStart == NSNotFound ? 0 : lineStart + 1
                let head = ns.substring(with: NSRange(location: ls, length: range.location - ls))
                let indent = String(head.prefix { $0 == " " || $0 == "\t" })
                let before = head.trimmingCharacters(in: .whitespaces)
                let after: String = range.location + range.length < ns.length
                    ? ns.substring(with: NSRange(location: range.location + range.length, length: 1)) : ""
                var insert = "\n" + indent
                var cursorBack = 0
                if before.hasSuffix("{") {
                    insert += "    "
                    if after == "}" { insert += "\n" + indent; cursorBack = indent.count + 1 }
                }
                tv.textStorage.replaceCharacters(in: range, with: insert)
                tv.selectedRange = NSRange(location: range.location + (insert as NSString).length - cursorBack, length: 0)
                textViewDidChange(tv)
                return false
            }
            if s == "}" && range.length == 0 {
                let lineStart = ns.range(of: "\n", options: .backwards, range: NSRange(location: 0, length: range.location)).location
                let ls = lineStart == NSNotFound ? 0 : lineStart + 1
                let head = ns.substring(with: NSRange(location: ls, length: range.location - ls))
                if head.count >= 4, head.allSatisfy({ $0 == " " }) {
                    tv.textStorage.replaceCharacters(in: NSRange(location: range.location - 4, length: 4), with: "}")
                    tv.selectedRange = NSRange(location: range.location - 3, length: 0)
                    textViewDidChange(tv)
                    return false
                }
            }
            if s == "\t" {
                tv.textStorage.replaceCharacters(in: range, with: "    ")
                tv.selectedRange = NSRange(location: range.location + 4, length: 0)
                textViewDidChange(tv)
                return false
            }
            return true
        }

        func keyRow(for tv: UITextView) -> UIView {
            let keys = ["tab", "{", "}", "(", ")", ";", "<", ">", "[", "]", "=", "+", "-", "*", "/", "&", "|", "!", "%", "^", "\"", "'", ":", ",", "_", "#", "\\"]
            let scroll = UIScrollView(frame: CGRect(x: 0, y: 0, width: 0, height: 44))
            scroll.showsHorizontalScrollIndicator = false
            scroll.backgroundColor = UIColor(Theme.sunk)
            let stack = UIStackView()
            stack.axis = .horizontal
            stack.spacing = 6
            stack.translatesAutoresizingMaskIntoConstraints = false
            for k in keys {
                let b = UIButton(type: .system)
                b.setTitle(k, for: .normal)
                b.titleLabel?.font = UIFont.monospacedSystemFont(ofSize: 15, weight: .regular)
                b.setTitleColor(UIColor(Theme.ink), for: .normal)
                b.backgroundColor = UIColor(Theme.paper)
                b.layer.cornerRadius = 6
                b.layer.borderWidth = 1
                b.layer.borderColor = UIColor(Theme.hairline).cgColor
                b.contentEdgeInsets = UIEdgeInsets(top: 4, left: 10, bottom: 4, right: 10)
                b.addAction(UIAction { [weak tv] _ in
                    guard let tv else { return }
                    tv.insertText(k == "tab" ? "    " : k)
                }, for: .touchUpInside)
                stack.addArrangedSubview(b)
            }
            scroll.addSubview(stack)
            NSLayoutConstraint.activate([
                stack.leadingAnchor.constraint(equalTo: scroll.contentLayoutGuide.leadingAnchor, constant: 8),
                stack.trailingAnchor.constraint(equalTo: scroll.contentLayoutGuide.trailingAnchor, constant: -8),
                stack.topAnchor.constraint(equalTo: scroll.contentLayoutGuide.topAnchor, constant: 6),
                stack.bottomAnchor.constraint(equalTo: scroll.contentLayoutGuide.bottomAnchor, constant: -6),
                stack.heightAnchor.constraint(equalTo: scroll.frameLayoutGuide.heightAnchor, constant: -12),
            ])
            return scroll
        }
    }
}

/// The editor in its box, with a line count.
struct EditorBox: View {
    @Binding var text: String
    var height: CGFloat = 340
    var body: some View {
        CodeEditor(text: $text)
            .frame(height: height)
            .background(Theme.raised)
            .overlay(RoundedRectangle(cornerRadius: 7).stroke(Theme.hairline))
            .clipShape(RoundedRectangle(cornerRadius: 7))
    }
}

/// Plain input for stdin and short answers.
struct PlainTextArea: View {
    @Binding var text: String
    var placeholder = ""
    var mono = true
    var height: CGFloat = 90
    var body: some View {
        ZStack(alignment: .topLeading) {
            if text.isEmpty {
                Text(placeholder).font(mono ? Theme.mono(13) : Theme.book(15.5)).foregroundStyle(Theme.faint)
                    .padding(.horizontal, 12).padding(.vertical, 12)
            }
            TextEditor(text: $text)
                .font(mono ? Theme.mono(13) : Theme.book(15.5))
                .foregroundStyle(Theme.ink)
                .scrollContentBackground(.hidden)
                .autocorrectionDisabled(mono)
                .textInputAutocapitalization(mono ? .never : .sentences)
                .keyboardType(mono ? .asciiCapable : .default)
                .padding(.horizontal, 7).padding(.vertical, 4)
        }
        .frame(height: height)
        .background(Theme.raised)
        .overlay(RoundedRectangle(cornerRadius: 6).stroke(Theme.hairline))
        .clipShape(RoundedRectangle(cornerRadius: 6))
    }
}
