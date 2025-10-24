"""
Issue categorization logic for EPIC system issues
"""

import re


def strip_metadata(text):
    """
    Remove common metadata patterns that shouldn't influence categorization.

    Args:
        text (str): Text to clean

    Returns:
        str: Text with metadata removed
    """
    # Patterns that indicate metadata, not actual issue content
    metadata_patterns = [
        r'account name[:\s]+[^\n]+',
        r'case\s*#[:\s]+\d+',
        r'policy number[:\s]+[^\n]+',
        r'policy type[:\s]+[^\n]+',
        r'policy period[:\s]+[^\n]+',
        r'insurer[:\s]+[^\n]+',
        r'policy term[:\s]+[^\n]+',
    ]

    cleaned = text
    for pattern in metadata_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    return cleaned


def categorize_issue(summary, description):
    """
    Categorize EPIC system issues into one of 8 core categories.
    Uses phrase-specific detection with metadata exclusion for high accuracy.

    Args:
        summary (str): Issue summary/title
        description (str): Issue description

    Returns:
        tuple: (category_name, confidence_score) where confidence is 0-100
    """
    # Handle None values
    summary_text = (summary or '').lower()
    desc_text = (description or '').lower()
    full_text = summary_text + ' ' + desc_text

    # Create a cleaned version without metadata for more accurate matching
    cleaned_text = strip_metadata(full_text)

    # ============================================================================
    # PHASE 1: Check for HIGHLY SPECIFIC PHRASES (98% confidence)
    # These are exact patterns that definitively identify the issue type
    # CHECK IN ORDER OF SPECIFICITY
    # ============================================================================

    # Account Cleanup/Removal - CHECK FIRST (most specific administrative action)
    cleanup_specific_phrases = [
        'please remove',
        'delete account',
        'remove account',
        'delete this account',
        'cleanup',
        'migration cleanup',
        'remove from 2.0',
        'remove from epic'
    ]
    for phrase in cleanup_specific_phrases:
        if phrase in full_text and ('account' in full_text or 'policy' in full_text):
            return ('Account Cleanup/Removal', 98)  # Very high confidence

    # Policy Header specific phrases - CHECK BEFORE generic policy
    header_specific_phrases = [
        'header not created',
        'header not in epic',
        'header not showing',
        'header not available',
        'policy header not created',
        'policy header not in epic',
        'header missing',
        'case issue# header',  # Common pattern
        'case issue: header',
        'case issue :header'
    ]
    for phrase in header_specific_phrases:
        if phrase in full_text:
            return ('Missing Policy Header', 98)  # Very high confidence

    # Policy specific phrases (NOT header, NOT cleanup)
    # IMPORTANT: Check these FIRST before falling back to keyword-based header detection
    policy_specific_phrases = [
        'policy is not in epic',
        'policy not in epic',
        'policy is not available',
        'policy not available',
        'policy not created',
        'policy not showing',
        'policy missing',
        'policy not found',
        'policy is missing',
        'policy did not migrate'
    ]

    # First, check if ANY policy-specific phrase exists (highest priority)
    for phrase in policy_specific_phrases:
        if phrase in full_text:
            # Found a policy-specific phrase!
            # Only skip if the SUMMARY explicitly mentions "header" (not just in metadata)
            if 'header' in summary_text or 'case issue# header' in full_text or 'case issue: header' in full_text:
                # This is actually about a header, skip to header logic
                break
            # Not about cleanup?
            if 'remove' not in full_text and 'delete' not in full_text:
                return ('Missing Policy', 98)  # Very high confidence

    # Policy type patterns: "[Type] policy is not in epic"
    policy_type_pattern = r'(worker[s]?\s+compensation|commercial\s+property|general\s+liability|auto|umbrella|liability|property|casualty|workers?\s+comp|wc|gl|comb\s+spec\s+ins)\s+policy\s+(is\s+)?(not\s+in\s+epic|missing|not\s+available|not\s+showing)'
    if re.search(policy_type_pattern, full_text, re.IGNORECASE):
        # Only skip if explicitly about header in the SUMMARY
        if 'header' not in summary_text and 'case issue# header' not in full_text:
            return ('Missing Policy', 98)  # Very high confidence - specific policy type missing

    # SSR specific phrases
    ssr_specific_phrases = [
        'ssr not created',
        'ssr not in epic',
        'ssr not showing',
        'ssr not available',
        'ssr missing',
        'ssr not visible',
        'ssr is not'
    ]
    for phrase in ssr_specific_phrases:
        if phrase in full_text:
            return ('Missing SSR', 98)  # Very high confidence

    # Account/Client specific phrases - BE SPECIFIC (not metadata)
    # Use cleaned_text to avoid matching metadata like "Account Name: XYZ"
    account_specific_phrases = [
        'account not created',
        'account not in epic',
        'account missing',
        'account is not available',
        'account not available',
        'client not in epic',
        'client missing',
        'client not found',
        'account not found',
        'unable to find given clients',
        'need a 2.0 account'
    ]
    for phrase in account_specific_phrases:
        if phrase in cleaned_text or phrase in full_text:
            return ('Account/Client Missing', 98)  # Very high confidence

    # ============================================================================
    # PHASE 2: Check for KEYWORDS with STRONG CONTEXT (90-95% confidence)
    # Single keywords with clear negative indicators
    # PRIORITY ORDER: Policy Header > Policy > Account > SSR
    # ============================================================================

    # Policy Header - check in summary or as explicit mention
    if 'header' in summary_text or 'policy header' in full_text:
        # Strong negative indicators
        negative_keywords = ['not', 'missing', 'incorrect', 'issue', 'not in epic',
                            'not updated', 'not created', 'not showing', 'error',
                            'unavailable', 'not available', 'not visible', 'is not']
        if any(keyword in full_text for keyword in negative_keywords):
            return ('Missing Policy Header', 95)  # High confidence
        return ('Missing Policy Header', 75)  # Medium-high confidence

    # Policy Missing - check BEFORE Account (more specific)
    if 'policy' in summary_text or 'policy' in cleaned_text:
        if 'header' not in full_text:  # Exclude header cases
            policy_missing_keywords = ['missing', 'not available', 'not in epic',
                                      'not showing', 'not found', 'not visible',
                                      'not created', 'is not', 'not migrate',
                                      'did not migrate', 'never set up']
            if any(keyword in full_text for keyword in policy_missing_keywords):
                return ('Missing Policy', 90)  # High confidence

    # Account/Client Missing - check in cleaned text (exclude metadata mentions)
    # Only match if it's the SUBJECT of the issue, not just mentioned in metadata
    if 'account' in cleaned_text or 'client' in cleaned_text:
        # Strong indicators this is about a missing account
        account_missing_keywords = ['missing', 'not found', 'not available', 'not showing',
                                   'not in epic', 'not visible', 'not created', 'locate',
                                   'unable to find', 'cannot find', 'need']
        if any(keyword in cleaned_text for keyword in account_missing_keywords):
            return ('Account/Client Missing', 90)  # High confidence

    # SSR issues
    if 'ssr' in summary_text or 'ssr' in desc_text:
        # Strong negative indicators
        negative_keywords = ['not', 'missing', 'unavailable', 'issue', 'not in epic',
                            'not available', 'not created', 'not showing', 'not visible',
                            'is not', 'error']
        if any(keyword in full_text for keyword in negative_keywords):
            return ('Missing SSR', 95)  # High confidence
        return ('Missing SSR', 70)  # Medium confidence

    # Producer Updates
    if 'producer' in summary_text or 'producer' in desc_text:
        producer_keywords = ['update', 'change', 'incorrect', 'wrong',
                           'not reflecting', 'not updated', 'needs update']
        if any(keyword in full_text for keyword in producer_keywords):
            return ('Producer Updates', 85)  # High confidence

    # Endorsement Issues
    if ('endorsement' in summary_text or 'endorse' in summary_text or
        'endorsement' in desc_text or 'endorse' in desc_text):
        return ('Endorsement Issues', 90)  # High confidence

    # ============================================================================
    # PHASE 3: BROADER KEYWORD MATCHING (70-80% confidence)
    # Less specific but still indicative
    # ============================================================================

    # Premium/Data Entry Issues
    premium_keywords = ['premium', 'data entry', 'data error', 'incorrect premium',
                       'wrong premium', 'amount', 'calculation', 'commission',
                       'accounting', 'invoice', 'billing']
    if any(keyword in full_text for keyword in premium_keywords):
        return ('Premium/Data Entry Issues', 80)  # Medium-high confidence

    # Renewal issues (could be endorsement or data entry)
    if 'renewal' in full_text or 'renew' in full_text:
        if 'not migrate' in full_text or 'did not migrate' in full_text:
            return ('Missing Policy', 75)  # Likely a missing renewal policy
        return ('Premium/Data Entry Issues', 70)  # General renewal issue

    # ============================================================================
    # PHASE 4: WEAK MATCHING (50-60% confidence)
    # Generic data-related keywords
    # ============================================================================

    data_keywords = ['data', 'entry', 'incorrect', 'wrong', 'error']
    if any(keyword in full_text for keyword in data_keywords):
        return ('Premium/Data Entry Issues', 55)  # Low confidence - weak match

    # ============================================================================
    # FINAL FALLBACK (40% confidence)
    # Should rarely reach here
    # ============================================================================

    return ('Premium/Data Entry Issues', 40)  # Low confidence - default fallback
