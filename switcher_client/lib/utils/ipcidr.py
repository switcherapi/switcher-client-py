class IPCIDR:
    """Class for checking if an IP address is within a CIDR range."""
    
    def __init__(self, cidr: str) -> None:
        """
        Initialize IPCIDR with a CIDR string.
        
        Args:
            cidr: CIDR notation string (e.g., '192.168.1.0/24')
        """
        self.cidr = cidr
    
    def _ip4_to_int(self, ip: str) -> int:
        """
        Convert an IPv4 address string to a 32-bit integer.
        
        Args:
            ip: IPv4 address string (e.g., '192.168.1.1')
            
        Returns:
            32-bit integer representation of the IP address
        """
        octets = ip.split('.')
        result = 0
        for octet in octets:
            result = (result << 8) + int(octet)
        return result & 0xFFFFFFFF  # Ensure 32-bit unsigned integer
    
    def is_ip4_in_cidr(self, ip: str) -> bool:
        """
        Check if an IPv4 address is within the CIDR range.
        
        Args:
            ip: IPv4 address string to check
            
        Returns:
            True if the IP is within the CIDR range, False otherwise
        """
        cidr_parts = self.cidr.split('/')
        range_ip = cidr_parts[0]
        bits = int(cidr_parts[1]) if len(cidr_parts) > 1 else 32
        
        mask = ~(2 ** (32 - bits) - 1) & 0xFFFFFFFF
        
        return (self._ip4_to_int(ip) & mask) == (self._ip4_to_int(range_ip) & mask)