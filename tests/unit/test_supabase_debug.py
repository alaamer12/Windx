"""Debug Supabase connection issues."""

import asyncio
import socket
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_dns_resolution():
    """Test DNS resolution with different methods."""
    hostname = "db.vglmnngcvcrdzvnaopde.supabase.co"
    
    print("=" * 60)
    print("DNS Resolution Tests")
    print("=" * 60)
    
    # Test 1: socket.getaddrinfo (what Python uses)
    print("\n1. Testing socket.getaddrinfo()...")
    try:
        addr_info = socket.getaddrinfo(hostname, 5432, socket.AF_UNSPEC, socket.SOCK_STREAM)
        print(f"✓ Resolved {len(addr_info)} addresses:")
        for info in addr_info:
            family = "IPv4" if info[0] == socket.AF_INET else "IPv6"
            print(f"  - {family}: {info[4][0]}")
    except socket.gaierror as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test 2: IPv4 only
    print("\n2. Testing IPv4 only resolution...")
    try:
        addr_info = socket.getaddrinfo(hostname, 5432, socket.AF_INET, socket.SOCK_STREAM)
        if addr_info:
            print(f"✓ IPv4 address: {addr_info[0][4][0]}")
        else:
            print("✗ No IPv4 address found")
    except socket.gaierror as e:
        print(f"✗ Failed: {e}")
    
    # Test 3: IPv6 only
    print("\n3. Testing IPv6 only resolution...")
    try:
        addr_info = socket.getaddrinfo(hostname, 5432, socket.AF_INET6, socket.SOCK_STREAM)
        if addr_info:
            print(f"✓ IPv6 address: {addr_info[0][4][0]}")
        else:
            print("✗ No IPv6 address found")
    except socket.gaierror as e:
        print(f"✗ Failed: {e}")
    
    # Test 4: gethostbyname (IPv4 only, legacy)
    print("\n4. Testing gethostbyname() [IPv4 only]...")
    try:
        ip = socket.gethostbyname(hostname)
        print(f"✓ IPv4 address: {ip}")
    except socket.gaierror as e:
        print(f"✗ Failed: {e}")
    
    return True


def test_tcp_connection():
    """Test raw TCP connection."""
    hostname = "db.vglmnngcvcrdzvnaopde.supabase.co"
    ports = [5432, 6543]
    
    print("\n" + "=" * 60)
    print("TCP Connection Tests")
    print("=" * 60)
    
    for port in ports:
        print(f"\nTesting port {port}...")
        try:
            # Try to resolve first
            addr_info = socket.getaddrinfo(hostname, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
            if not addr_info:
                print(f"✗ No addresses resolved")
                continue
            
            # Try to connect to first address
            family, socktype, proto, canonname, sockaddr = addr_info[0]
            print(f"  Attempting connection to {sockaddr[0]}:{sockaddr[1]}...")
            
            sock = socket.socket(family, socktype, proto)
            sock.settimeout(5)
            
            try:
                sock.connect(sockaddr)
                print(f"✓ TCP connection successful!")
                sock.close()
            except socket.timeout:
                print(f"✗ Connection timeout")
            except ConnectionRefusedError:
                print(f"✗ Connection refused")
            except Exception as e:
                print(f"✗ Connection failed: {e}")
            
        except socket.gaierror as e:
            print(f"✗ DNS resolution failed: {e}")
        except Exception as e:
            print(f"✗ Error: {e}")


async def test_asyncpg_connection():
    """Test asyncpg connection directly."""
    print("\n" + "=" * 60)
    print("AsyncPG Connection Test")
    print("=" * 60)
    
    try:
        import asyncpg
    except ImportError:
        print("✗ asyncpg not installed")
        return False
    
    hostname = "db.vglmnngcvcrdzvnaopde.supabase.co"
    
    for port in [5432, 6543]:
        print(f"\nTesting port {port}...")
        try:
            conn = await asyncpg.connect(
                host=hostname,
                port=port,
                user="postgres",
                password="DhsRZdcOMMxhrzwY",
                database="postgres",
                timeout=10,
                command_timeout=10,
            )
            
            version = await conn.fetchval("SELECT version()")
            print(f"✓ Connection successful!")
            print(f"  Version: {version[:80]}...")
            
            await conn.close()
            return True
            
        except asyncpg.exceptions.InvalidPasswordError:
            print(f"✗ Invalid password")
        except asyncpg.exceptions.InvalidCatalogNameError:
            print(f"✗ Invalid database name")
        except asyncio.TimeoutError:
            print(f"✗ Connection timeout")
        except Exception as e:
            print(f"✗ Failed: {type(e).__name__}: {e}")
    
    return False


def main():
    """Run all diagnostic tests."""
    print("\n" + "=" * 60)
    print("SUPABASE CONNECTION DIAGNOSTICS")
    print("=" * 60)
    
    # Test DNS
    dns_ok = test_dns_resolution()
    
    if not dns_ok:
        print("\n" + "=" * 60)
        print("DIAGNOSIS: DNS Resolution Failed")
        print("=" * 60)
        print("\nPossible causes:")
        print("1. No internet connection")
        print("2. DNS server issues")
        print("3. Firewall blocking DNS queries")
        print("4. Invalid hostname")
        print("\nSolutions:")
        print("1. Check internet connection")
        print("2. Try changing DNS to 8.8.8.8 (Google DNS)")
        print("3. Flush DNS cache: ipconfig /flushdns")
        print("4. Restart network adapter")
        return
    
    # Test TCP
    test_tcp_connection()
    
    # Test asyncpg
    asyncio.run(test_asyncpg_connection())
    
    print("\n" + "=" * 60)
    print("DIAGNOSTICS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
