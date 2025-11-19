 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/services/translator.py b/services/translator.py
new file mode 100644
index 0000000000000000000000000000000000000000..fffeee43670a30524445e6c2356ab9fc0de0a290
--- /dev/null
+++ b/services/translator.py
@@ -0,0 +1,92 @@
+"""Translation utilities used by the marketplace chat views.
+
+The app attempts to use ``deep_translator`` to provide real translations when
+network access is available.  When the dependency cannot be used (for example in
+restricted CI environments) the ``FallbackDictionary`` ensures a predictable and
+fully offline experience by translating a curated list of phrases and
+sentences.  Unknown strings are wrapped in a descriptive message to make it
+clear that an automatic translation was not possible.
+"""
+from __future__ import annotations
+
+from dataclasses import dataclass
+from typing import Dict, Tuple
+
+try:  # pragma: no cover - optional dependency
+    from deep_translator import GoogleTranslator  # type: ignore
+except Exception:  # pragma: no cover - gracefully handle missing dependency
+    GoogleTranslator = None
+
+
+@dataclass
+class TranslationResult:
+    original: str
+    translated: str
+    source_language: str
+    target_language: str
+
+
+class FallbackDictionary:
+    """Very small offline dictionary.
+
+    The goal is not to be perfect, but to keep the UI functional when external
+    services are unavailable.  The dictionary is intentionally tiny to keep the
+    repository light-weight, yet the helper makes it straightforward to expand
+    when needed.
+    """
+
+    def __init__(self) -> None:
+        self._entries: Dict[Tuple[str, str, str], str] = {}
+        self.add_bulk({
+            ("en", "ko", "hello"): "안녕하세요",
+            ("en", "es", "hello"): "hola",
+            ("ko", "en", "안녕하세요"): "hello",
+            ("es", "en", "hola"): "hello",
+            ("en", "ko", "thank you"): "감사합니다",
+            ("en", "es", "thank you"): "gracias",
+            ("es", "ko", "gracias"): "감사합니다",
+            ("ko", "es", "감사합니다"): "gracias",
+        })
+
+    def add_bulk(self, entries: Dict[Tuple[str, str, str], str]) -> None:
+        self._entries.update(entries)
+
+    def translate(self, text: str, source: str, target: str) -> str | None:
+        key = (source.lower(), target.lower(), text.strip().lower())
+        return self._entries.get(key)
+
+
+class Translator:
+    """Small facade that keeps translation related logic in a single place."""
+
+    def __init__(self) -> None:
+        self._fallback = FallbackDictionary()
+
+    def translate(self, text: str, source_language: str, target_language: str) -> TranslationResult:
+        source = (source_language or "en").lower()
+        target = (target_language or "en").lower()
+        if source == target:
+            return TranslationResult(text, text, source, target)
+
+        translated = self._translate_with_service(text, source, target)
+        if translated is None:
+            translated = self._translate_with_dictionary(text, source, target)
+        if translated is None:
+            translated = f"[translation unavailable → {target}] {text}"
+        return TranslationResult(text, translated, source, target)
+
+    def _translate_with_service(self, text: str, source: str, target: str) -> str | None:
+        if not GoogleTranslator:
+            return None
+        try:  # pragma: no cover - runtime only
+            translator = GoogleTranslator(source=source, target=target)
+            return translator.translate(text)
+        except Exception:
+            return None
+
+    def _translate_with_dictionary(self, text: str, source: str, target: str) -> str | None:
+        return self._fallback.translate(text, source, target)
+
+
+translator = Translator()
+"""Shared translator instance used by the Flask views."""
 
EOF
)
