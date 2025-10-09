"""
Issue categorization logic for EPIC system issues
"""

def categorize_issue(summary, description):
    """
    Categorize EPIC system issues into one of 7 core categories.

    Args:
        summary (str): Issue summary/title
        description (str): Issue description

    Returns:
        str: Category name
    """
    # Handle None values
    summary_text = (summary or '').lower()
    desc_text = (description or '').lower()
    full_text = summary_text + ' ' + desc_text

    # PRIORITY 1: Check for SSR issues - be very thorough
    if 'ssr' in summary_text or 'ssr' in desc_text:
        # Any SSR mention with negative context
        negative_keywords = ['not', 'missing', 'unavailable', 'issue', 'not in epic',
                            'not available', 'not created', 'not showing', 'not visible', 'is not']
        if any(keyword in full_text for keyword in negative_keywords):
            return 'Missing SSR'
        # Even if just "SSR" appears without clear positive context, likely a missing SSR issue
        return 'Missing SSR'

    # PRIORITY 2: Check for Policy Header issues - be very thorough
    if 'header' in summary_text or 'policy header' in desc_text:
        # Any header mention with negative context
        negative_keywords = ['not', 'missing', 'incorrect', 'issue', 'not in epic',
                            'not updated', 'not created', 'not showing', 'error']
        if any(keyword in full_text for keyword in negative_keywords):
            return 'Missing Policy Header'
        # Header mention likely indicates a header issue
        return 'Missing Policy Header'

    # PRIORITY 3: Check for Account/Client Missing
    if ('account' in summary_text or 'client' in summary_text):
        missing_keywords = ['missing', 'not found', 'not available', 'not showing',
                          'not in epic', 'not visible']
        if any(keyword in full_text for keyword in missing_keywords):
            return 'Account/Client Missing'

    # PRIORITY 4: Check for Policy Missing (be specific - not just any policy mention)
    if 'policy' in summary_text and 'header' not in summary_text:
        if 'policy' in full_text:
            policy_missing_keywords = ['missing', 'not available', 'not in epic',
                                      'not showing', 'not found', 'not visible']
            if any(keyword in full_text for keyword in policy_missing_keywords):
                return 'Missing Policy'

    # PRIORITY 5: Check for Producer Updates
    if 'producer' in summary_text or 'producer' in desc_text:
        producer_keywords = ['update', 'change', 'incorrect', 'wrong',
                           'not reflecting', 'not updated']
        if any(keyword in full_text for keyword in producer_keywords):
            return 'Producer Updates'

    # PRIORITY 6: Check for Endorsement Issues
    if ('endorsement' in summary_text or 'endorse' in summary_text or
        'endorsement' in desc_text or 'endorse' in desc_text):
        return 'Endorsement Issues'

    # PRIORITY 7: Premium/Data Entry Issues - be specific
    premium_keywords = ['premium', 'data entry', 'data error', 'incorrect premium',
                       'wrong premium', 'amount', 'calculation']
    if any(keyword in full_text for keyword in premium_keywords):
        return 'Premium/Data Entry Issues'

    # FINAL CATCH-ALL: If we still don't have a category, analyze the issue type
    # Check for any data-related keywords
    data_keywords = ['data', 'entry', 'incorrect', 'wrong', 'error']
    if any(keyword in full_text for keyword in data_keywords):
        return 'Premium/Data Entry Issues'

    # True default - should rarely reach here
    return 'Premium/Data Entry Issues'
