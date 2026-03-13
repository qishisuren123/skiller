# Type-safe field validation
for field in required_fields:
    if entry[field] is None:
        return False, f"Field {field} is null"
    if not isinstance(entry[field], str):
        try:
            entry[field] = str(entry[field])
        except:
            return False, f"Field {field} cannot be converted to string"

# Memory-safe text processing
def normalize_text(text, max_words=200):
    words = text.split()
    if len(words) > max_words:
        text = ' '.join(words[:max_words])
    return text

# Two-stage duplicate detection
if has_potential_overlap(text1, text2, threshold=0.3):
    similarity = calculate_similarity(text1, text2)
    if similarity > 0.9:
        # Handle duplicate

# Safe average calculation
if final_entries:
    avg_len = sum(len(entry['field']) for entry in final_entries) / len(final_entries)
else:
    avg_len = 0
