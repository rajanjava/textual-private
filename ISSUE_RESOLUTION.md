# Issue Resolution: Matcher(case_sensitive=True) Matches Case-Insensitively (#6775)

## 1. Upstream Issue Metadata
- **Repository:** `Textualize/textual`
- **Issue Reference:** [#6775 - `Matcher(case_sensitive=True)` still matches case-insensitively](https://github.com/Textualize/textual/issues/6775)
- **Component:** `src/textual/fuzzy.py` (`Matcher.__init__`, `FuzzySearch.match`)
- **Severity / Impact:** High (Filtering & Command Palette Logic Corruption). When creating a `Matcher` or using `Provider.matcher(user_input, case_sensitive=True)` in Textual's command palette or search widgets, the `case_sensitive` setting was ignored and matching remained completely case-insensitive. Furthermore, `FuzzySearch` cached queries without considering `case_sensitive`, yielding stale matches upon attribute mutation.

---

## 2. Root Cause Analysis
1. In `Matcher.__init__`:
   ```python
   self._case_sensitive = case_sensitive
   self.fuzzy_search = FuzzySearch()
   ```
   While `case_sensitive` was received as an argument and assigned to private variable `_case_sensitive`, `FuzzySearch()` was instantiated with zero arguments, which defaulted to `case_sensitive=False`.
2. As a consequence, `self.fuzzy_search.case_sensitive` was always `False`, rendering `Matcher(..., case_sensitive=True)` inert.
3. In `FuzzySearch.match`:
   ```python
   cache_key = (query, candidate)
   ```
   The cache key omitted `self.case_sensitive`. Modifying `case_sensitive` on a `FuzzySearch` instance returned stale results from previous queries.

---

## 3. Reproduction Test
In `tests/test_fuzzy.py`:
```python
def test_matcher_case_sensitive():
    matcher = Matcher("foo", case_sensitive=True)
    assert matcher.match("FOO") == 0.0
    assert matcher.match("foo") > 0.0


def test_fuzzy_search_cache_case_sensitive():
    search = FuzzySearch()
    score_insensitive, _ = search.match("foo", "FOO")
    assert score_insensitive > 0.0
    search.case_sensitive = True
    score_sensitive, _ = search.match("foo", "FOO")
    assert score_sensitive == 0.0
```

### Pre-Fix Failure Output:
```text
FAILED tests/test_fuzzy.py::test_matcher_case_sensitive - AssertionError: assert 16.0 == 0.0
FAILED tests/test_fuzzy.py::test_fuzzy_search_cache_case_sensitive - assert 16.0 == 0.0
```

---

## 4. Implementation Diff
```diff
diff --git a/src/textual/fuzzy.py b/src/textual/fuzzy.py
index 34c518c..1f9f11e 100644
--- a/src/textual/fuzzy.py
+++ b/src/textual/fuzzy.py
@@ -51,7 +51,7 @@ class FuzzySearch:
             A pair of (score, tuple of offsets). `(0, ())` for no result.
         """
 
-        cache_key = (query, candidate)
+        cache_key = (query, candidate, self.case_sensitive)
         if cache_key in self.cache:
             return self.cache[cache_key]
         default: tuple[float, Sequence[int]] = (0.0, [])
@@ -172,7 +172,7 @@ class Matcher:
         self._query = query
         self._match_style = Style(reverse=True) if match_style is None else match_style
         self._case_sensitive = case_sensitive
-        self.fuzzy_search = FuzzySearch()
+        self.fuzzy_search = FuzzySearch(case_sensitive=case_sensitive)
 
     @property
     def query(self) -> str:
```

---

## 5. Verification Results
- **Reproduction Tests:** Both `test_matcher_case_sensitive` and `test_fuzzy_search_cache_case_sensitive` passed.
- **Fuzzy Search Suite:** `pytest tests/test_fuzzy.py` passed (6 passed in 0.13s).
- **Command Palette Suite:** `pytest tests/command_palette/` passed (22 passed in 4.68s, 0 regressions).
- **Ruff Lint Check:** `ruff check src/textual/fuzzy.py tests/test_fuzzy.py` passed with 0 errors.
