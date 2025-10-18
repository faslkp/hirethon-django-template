# Bulk Upload Excel Template

Create an Excel file (.xlsx) with the following structure for bulk URL shortening:

## Required Column:
- **original_url**: The full URL to be shortened (e.g., https://example.com/very/long/url)

## Optional Column:
- **custom_short_code**: Your desired short code (e.g., my-custom-code)
  - If left empty, a random code will be generated
  - Must be unique within the namespace
  - Use only lowercase letters, numbers, and hyphens

## Example:

| original_url | custom_short_code |
|-------------|-------------------|
| https://example.com/page1 | page1 |
| https://example.com/page2 | special-link |
| https://example.com/page3 |  |

## Notes:
- The first row must contain the column headers
- Empty custom_short_code cells will auto-generate codes
- All URLs in a single upload must belong to the same namespace
- Invalid rows will be marked as failed in the output file

## Output File:

After processing, you'll receive an Excel file with these columns:
- **original_url**: The original URL
- **short_code**: The generated or custom short code
- **short_url**: The full shortened URL path
- **status**: SUCCESS or FAILED
- **error**: Error message (if any)

