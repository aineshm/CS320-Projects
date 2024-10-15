import pandas as pd
from bisect import bisect_left
import netaddr
import re

# Read the CSV file and preprocess the data
def load_ip_data(csv_file_path):
    ip_data = pd.read_csv(csv_file_path)
    ip_ranges = list(zip(ip_data['low'], ip_data['high'], ip_data['code'], ip_data['region']))
    return ip_ranges

# Preprocessed IP ranges
ip_ranges = load_ip_data('./ip2location.csv')

# Binary search function
def find_ip_range(ip_int, ip_ranges):
    left = 0
    right = len(ip_ranges) - 1
    while left <= right:
        mid = (left + right) // 2
        if ip_ranges[mid][0] <= ip_int <= ip_ranges[mid][1]:
            return ip_ranges[mid][2], ip_ranges[mid][3]  # Return the country code and country name
        elif ip_int < ip_ranges[mid][0]:
            right = mid - 1
        else:
            left = mid + 1
    return None, None  # Not found

# Function to replace letters in an IP address with "0"
def anonymize_ip(ip_address):
    return re.sub(r'[a-zA-Z]', '0', ip_address)

# Lookup region function
def lookup_region(ip_address):
    anonymized_ip = anonymize_ip(ip_address)
    try:
        ip_int = int(netaddr.IPAddress(anonymized_ip))
        country_code, country_name = find_ip_range(ip_int, ip_ranges)
        return country_name if country_name else "Unknown"
    except (netaddr.AddrFormatError, ValueError):
        return "Invalid IP address"
    
    
class Filing:
    def __init__(self, html):
        self.dates = self.extract_dates(html)
        self.sic = self.extract_sic(html)
        self.addresses = self.extract_addresses(html)
    
    def extract_dates(self, html):
        date_tuples = re.findall(r'\b(19|20)\d{2}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])\b', html)
        return ['-'.join(date) for date in date_tuples]
    
    def extract_sic(self, html):
        sic_codes = re.findall(r'SIC=([0-9]+)', html)
        return int(sic_codes[0]) if sic_codes else None
    
    def extract_addresses(self, html):
        address_divs = re.findall(r'<div class="mailer">([\s\S]+?)</div>', html)
        addresses = []
        for addr_html in address_divs:
            lines = re.findall(r'<span class="mailerAddress">([\s\S]+?)</span>', addr_html)
            cleaned_lines = [line.strip() for line in lines]
            if cleaned_lines:
                addresses.append('\n'.join(cleaned_lines))
        return addresses
    
    def state(self):
        state_regex = re.compile(r'\b[A-Z]{2} \d{5}\b')
        for address in self.addresses:
            match = state_regex.search(address)
            if match:
                return match.group().split()[0]
        return None