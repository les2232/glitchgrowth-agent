from typing import Dict, List

def check_compliance(
    sponsored: bool,
    gifted: bool,
    affiliate: bool,
    brand_relationship: bool,
) -> Dict[str, object]:
    flags: List[str] = []
    if sponsored:
        flags.append("sponsored")
    if gifted:
        flags.append("gifted")
    if affiliate:
        flags.append("affiliate")
    if brand_relationship:
        flags.append("brand relationship")

    needs_disclosure = bool(flags)

    if not needs_disclosure:
        return {
            "needs_disclosure": False,
            "flags": [],
            "guidance": "No monetized relationship selected. No special disclosure reminder triggered.",
            "sample_disclosures": [],
        }

    samples = []
    if sponsored or brand_relationship:
        samples.append("Sponsored / paid partnership with [Brand].")
    if gifted:
        samples.append("Gifted by [Brand].")
    if affiliate:
        samples.append("Affiliate link — I may earn a commission if you buy through this link.")

    return {
        "needs_disclosure": True,
        "flags": flags,
        "guidance": (
            "Add a clear disclosure near the beginning of the caption or visibly in the content. "
            "Do not hide the disclosure deep in hashtags or vague wording."
        ),
        "sample_disclosures": samples,
    }
