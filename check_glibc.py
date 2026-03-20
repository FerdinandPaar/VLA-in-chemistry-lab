import pexpect
import sys

PASSWORD = "Ferdi1811!"
GRIDMASTER = "gridmaster"
# Command to check GLIBC version
CMD = "qrsh -q mld.q@gridnode016 -now n 'ldd --version'"

def main():
    print(f"Connecting to {GRIDMASTER}...")
    child = pexpect.spawn(f"ssh -q {GRIDMASTER}", encoding='utf-8')
    
    i = child.expect(['Password:', 'password:', pexpect.EOF, pexpect.TIMEOUT], timeout=30)
    if i == 0 or i == 1:
        child.sendline(PASSWORD)
    
    child.expect(['\$', '#', '>'], timeout=30)
    print("Logged in!")

    print(f"Sending command: {CMD}")
    child.sendline(CMD)
    
    try:
        # Expect output
        child.expect(pexpect.EOF, timeout=10) # Just read everything until it closes or timeouts
    except:
        pass
        
    print(child.before)
    child.close()

if __name__ == "__main__":
    main()
