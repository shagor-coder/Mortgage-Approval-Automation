import re
from typing import Dict, Optional, Union
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IncomeExtractor:
    def __init__(self):
        # W2 patterns remain unchanged
        self.w2_patterns = {
            'wages_and_tips': [
                r'box\s*1.*?\$?\s*(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                r'wages,?\s*tips.*?\$?\s*(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                r'wages\s+and\s+tips.*?\$?\s*(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                r'compensation.*?\$?\s*(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                r'\$\s*(\d{1,3}(?:,\d{3})*\.?\d{0,2}).*?box\s*1',
                r'\$\s*(\d{1,3}(?:,\d{3})*\.?\d{0,2}).*?wages'
            ],
            'social_security_wages': [
                r'box\s*3.*?\$?\s*(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                r'social\s+security\s+wages.*?\$?\s*(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                r'\$\s*(\d{1,3}(?:,\d{3})*\.?\d{0,2}).*?box\s*3',
                r'\$\s*(\d{1,3}(?:,\d{3})*\.?\d{0,2}).*?social security'
            ],
            'medicare_wages': [
                r'box\s*5.*?\$?\s*(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                r'medicare\s+wages.*?\$?\s*(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                r'\$\s*(\d{1,3}(?:,\d{3})*\.?\d{0,2}).*?box\s*5',
                r'\$\s*(\d{1,3}(?:,\d{3})*\.?\d{0,2}).*?medicare'
            ]
        }

        # Enhanced paystub patterns
        self.paystub_patterns = {
            'gross_pay': [
                r'(?:gross|total gross|gross amount).*?(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                r'(?:salary|pay rate).*?(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                r'(?:regular).*?(?:pay|earnings).*?(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                r'(?:pay\s+period|period\s+pay).*?(\d{1,3}(?:,\d{3})*\.?\d{0,2})'
            ],
            'ytd_earnings': [
                r'(?:ytd|year.*?to.*?date|y-t-d).*?(?:gross|earnings|pay|income).*?(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                r'(?:total.*?ytd|ytd.*?total).*?(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                r'(?:current.*?ytd|ytd.*?current).*?(\d{1,3}(?:,\d{3})*\.?\d{0,2})'
            ],
            'net_pay': [
                r'(?:net\s+pay|take\s+home|net\s+amount).*?(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                r'(?:total\s+net|net\s+total).*?(\d{1,3}(?:,\d{3})*\.?\d{0,2})'
            ],
            'hours': [
                r'(?:regular|total)\s+hours.*?(\d+\.?\d*)',
                r'hours.*?worked.*?(\d+\.?\d*)',
                r'(?:period|current).*?hours.*?(\d+\.?\d*)'
            ],
            'rate': [
                r'(?:hourly|hour|hr)\s+rate.*?(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                r'rate.*?(?:per|/)\s*(?:hour|hr).*?(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                r'(\d{1,3}(?:,\d{3})*\.?\d{0,2}).*?(?:per|/)\s*(?:hour|hr)'
            ]
        }

        # Date patterns
        self.date_patterns = {
            'period_ending': [
                r'(?:period\s+end(?:ing)?|end(?:ing)?\s+date|pay\s+date).*?(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'(?:period\s+end(?:ing)?|end(?:ing)?\s+date|pay\s+date).*?(\w+\s+\d{1,2},?\s*\d{4})'
            ]
        }

        # Pay frequency indicators
        self.frequency_patterns = [
            (r'weekly|per\s+week|(?:per|/)\s*wk', 52),
            (r'biweekly|bi-weekly|bi\s+weekly|every\s+two\s+weeks', 26),
            (r'semi.?monthly|twice\s+per\s+month', 24),
            (r'monthly|per\s+month|(?:per|/)\s*mo', 12),
            (r'quarterly|per\s+quarter', 4),
            (r'annually|annual|yearly|per\s+year|(?:per|/)\s*yr', 1)
        ]

        self.generic_patterns = {
            'monetary_amounts': [
                r'(?:total|amount|income|earnings|salary|pay|compensation).*?(?:[\$\:]|\:\s+)?\s*(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                r'(?:biweekly|weekly|monthly|annual|quarterly|hourly).*?(?:rate|salary|pay).*?(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                r'(?:regular|overtime|bonus|commission).*?(?:pay|rate|hours).*?(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                r'\$\s*(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                r'(\d{1,3}(?:,\d{3})*\.?\d{0,2})\s*(?:usd|dollars|\$)',
                r'(?:per|/)\s*(?:hour|hr|week|month|year|annum).*?(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                r'(\d{1,3}(?:,\d{3})*\.?\d{0,2})\s*(?:per|/)\s*(?:hour|hr|week|month|year|annum)'
            ]
        }

    def _clean_amount(self, amount_str: str) -> float:
        """Convert string amount to float, removing commas and handling missing decimals"""
        try:
            # Remove any non-numeric characters except dots and commas
            cleaned = re.sub(r'[^\d.,]', '', amount_str)
            cleaned = cleaned.replace(',', '')
            if '.' not in cleaned:
                cleaned += '.00'
            if cleaned.endswith('.'):
                cleaned += '00'
            elif len(cleaned.split('.')[1]) == 1:
                cleaned += '0'
            return float(cleaned)
        except (ValueError, AttributeError) as e:
            logger.error(f"Error converting amount {amount_str}: {str(e)}")
            return 0.0

    def _find_highest_amount(self, text: str, patterns: list) -> Optional[float]:
        """Find the highest matching amount using multiple patterns"""
        text = text.lower()
        highest_amount = 0.0

        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                if match and match.group(1):
                    amount = self._clean_amount(match.group(1))
                    if amount > highest_amount:
                        highest_amount = amount
                        logger.info(f"Found higher amount {amount} using pattern {pattern}")

        return highest_amount if highest_amount > 0 else None

    def _detect_pay_frequency(self, text: str) -> int:
        """Detect pay frequency and return number of pay periods per year"""
        text = text.lower()
        for pattern, frequency in self.frequency_patterns:
            if re.search(pattern, text):
                logger.info(f"Detected pay frequency: {pattern} ({frequency} periods/year)")
                return frequency
        # Default to biweekly if no frequency detected
        logger.info("No pay frequency detected, defaulting to biweekly (26 periods/year)")
        return 26

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string into datetime object"""
        try:
            # Try different date formats
            formats = [
                '%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d',
                '%m/%d/%y', '%m-%d-%y', '%y-%m-%d',
                '%B %d, %Y', '%b %d, %Y'
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            return None
        except Exception as e:
            logger.error(f"Error parsing date {date_str}: {str(e)}")
            return None

    def _find_date(self, text: str, patterns: list) -> Optional[str]:
        """Find the first matching date using multiple patterns"""
        text = text.lower()
        for pattern in patterns:
            match = re.search(pattern, text)
            if match and match.group(1):
                logger.info(f"Found date: {match.group(1)}")
                return match.group(1)
        return None

    def extract_w2_income(self, text: str) -> Dict[str, float]:
        """Extract income information from W2 text"""
        logger.info("Extracting W2 income information")
        result = {}
        logger.info(f"Processing W2 text: {text[:500]}...")

        for field, patterns in self.w2_patterns.items():
            amount = self._find_highest_amount(text, patterns)
            if amount is not None:
                result[field] = amount
                logger.info(f"Found {field}: ${amount:,.2f}")
            else:
                logger.warning(f"Could not find amount for {field}")
                result[field] = 0.0

        return result

    def extract_paystub_income(self, text: str) -> Dict[str, Union[float, str, int]]:
        """Extract income information from paystub text including pay frequency and dates"""
        logger.info("Extracting paystub income information")
        result = {}

        # Extract basic amounts
        for field, patterns in self.paystub_patterns.items():
            amount = self._find_highest_amount(text, patterns)
            if amount is not None:
                result[field] = amount
                logger.info(f"Found {field}: {amount}")
            else:
                logger.warning(f"Could not find amount for {field}")
                result[field] = 0.0

        # Extract pay period end date
        period_end = self._find_date(text, self.date_patterns['period_ending'])
        if period_end:
            result['period_ending'] = period_end

        # Detect pay frequency
        pay_frequency = self._detect_pay_frequency(text)
        result['pay_frequency'] = pay_frequency

        # Calculate annualized and monthly income
        gross_pay = result.get('gross_pay', 0)
        ytd_earnings = result.get('ytd_earnings', 0)
        hours = result.get('hours', 0)
        rate = result.get('rate', 0)

        # Try different methods to calculate annualized income
        annualized_amounts = []

        # Method 1: Using current period gross pay and frequency
        if gross_pay > 0 and pay_frequency > 0:
            annualized = gross_pay * pay_frequency
            annualized_amounts.append(('pay_frequency', annualized))
            logger.info(f"Calculated annualized income from pay frequency: ${annualized:,.2f}")

        # Method 2: Using YTD earnings and period end date
        if ytd_earnings > 0 and period_end:
            parsed_date = self._parse_date(period_end)
            if parsed_date:
                days_in_year = 365
                days_elapsed = parsed_date.timetuple().tm_yday
                if days_elapsed > 0:
                    annualized = (ytd_earnings / days_elapsed) * days_in_year
                    annualized_amounts.append(('ytd_projection', annualized))
                    logger.info(f"Calculated annualized income from YTD: ${annualized:,.2f}")

        # Method 3: Using hourly rate and hours
        if hours > 0 and rate > 0:
            annualized = hours * rate * 52  # Assuming consistent weekly hours
            annualized_amounts.append(('hourly_rate', annualized))
            logger.info(f"Calculated annualized income from hourly rate: ${annualized:,.2f}")

        # Select the most reliable annualized amount
        if annualized_amounts:
            # Prefer YTD projection if available, otherwise use the highest amount
            ytd_projection = next((amount for method, amount in annualized_amounts if method == 'ytd_projection'), None)
            if ytd_projection:
                result['annualized_income'] = ytd_projection
            else:
                result['annualized_income'] = max(amount for _, amount in annualized_amounts)

            # Calculate monthly income
            result['monthly_income'] = result['annualized_income'] / 12
            logger.info(f"Final annualized income: ${result['annualized_income']:,.2f}")
            logger.info(f"Monthly income: ${result['monthly_income']:,.2f}")
        else:
            logger.warning("Could not calculate annualized income")
            result['annualized_income'] = 0
            result['monthly_income'] = 0

        return result

    def extract_generic_income(self, text: str) -> Dict[str, Union[float, list]]:
        """Extract income information from unknown document types with improved context analysis"""
        logger.info("Extracting generic income information")

        # Initialize result dictionary with more detailed structure
        result = {
            'detected_amounts': [],
            'potential_income_amounts': [],
            'highest_amount': 0,
            'total_amounts_found': 0,
            'confidence_level': 'low'
        }

        # Enhanced income-related keywords
        income_keywords = {
            'high_confidence': [
                'salary', 'annual income', 'monthly income', 'yearly income',
                'base pay', 'compensation', 'earnings'
            ],
            'medium_confidence': [
                'payment', 'rate', 'wages', 'pay rate', 'gross', 'net',
                'biweekly', 'weekly', 'monthly'
            ],
            'low_confidence': [
                'total', 'amount', 'sum', 'payment', 'balance'
            ]
        }

        # Process text to find monetary amounts with context
        text = text.lower()
        for field, patterns in self.generic_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    if match and match.group(1):
                        amount = self._clean_amount(match.group(1))
                        if amount > 0:
                            # Get surrounding context (100 characters before and after)
                            start = max(0, match.start() - 100)
                            end = min(len(text), match.end() + 100)
                            context = text[start:end].strip()

                            # Analyze context for income-related keywords
                            confidence = 'low'
                            if any(keyword in context for keyword in income_keywords['high_confidence']):
                                confidence = 'high'
                            elif any(keyword in context for keyword in income_keywords['medium_confidence']):
                                confidence = 'medium'

                            amount_info = {
                                'amount': amount,
                                'context': context,
                                'confidence': confidence
                            }

                            result['detected_amounts'].append(amount_info)

                            # Track highest amount
                            if amount > result['highest_amount']:
                                result['highest_amount'] = amount

                            # If high or medium confidence, add to potential income amounts
                            if confidence in ['high', 'medium']:
                                result['potential_income_amounts'].append(amount_info)

        # Update total amounts found
        result['total_amounts_found'] = len(result['detected_amounts'])

        # Sort amounts by confidence and value
        if result['potential_income_amounts']:
            result['potential_income_amounts'].sort(
                key=lambda x: (
                    {'high': 2, 'medium': 1, 'low': 0}[x['confidence']],
                    x['amount']
                ),
                reverse=True
            )

            # Set overall confidence level based on findings
            if any(x['confidence'] == 'high' for x in result['potential_income_amounts']):
                result['confidence_level'] = 'high'
            elif any(x['confidence'] == 'medium' for x in result['potential_income_amounts']):
                result['confidence_level'] = 'medium'

            # Add most likely income amount if found
            if result['potential_income_amounts']:
                result['most_likely_income'] = result['potential_income_amounts'][0]

        logger.info(f"Found {result['total_amounts_found']} amounts, "
                    f"confidence level: {result['confidence_level']}")

        return result

    def extract_income(self, text: str, doc_type: str) -> Dict[str, Union[float, str, int, list]]:
        """Extract income based on document type"""
        if doc_type == 'W2':
            return self.extract_w2_income(text)
        elif doc_type == 'Paystub':
            return self.extract_paystub_income(text)
        else:
            logger.info(f"Using generic extraction for document type: {doc_type}")
            return self.extract_generic_income(text)