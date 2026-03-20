import pexpect
import sys
import time

PASSWORD = "Ferdi1811!"
GRIDMASTER = "gridmaster"
# We need to source conda in the remote shell
SERVER_CMD = "qrsh -q mld.q@gridnode016 -now n 'source ~/miniconda3/etc/profile.d/conda.sh && conda activate smolvla && cd ~/Projects/Lerobot && python -u inference_server.py 2>&1'"

def main():
    print(f"Connecting to {GRIDMASTER}...")
    child = pexpect.spawn(f"ssh -q -L 5555:gridnode016:5555 {GRIDMASTER}", encoding='utf-8')
    
    # Handle password prompt
    i = child.expect(['Password:', 'password:', pexpect.EOF, pexpect.TIMEOUT], timeout=30)
    if i == 0 or i == 1:
        print("Sending password...")
        child.sendline(PASSWORD)
    elif i == 2:
        print("EOF received before password prompt")
        print(child.before)
        sys.exit(1)
    elif i == 3:
        print("Timeout waiting for password prompt")
        print(child.before)
        sys.exit(1)
        
    # Wait for prompt (assuming shell prompt ends with $ or # or >)
    # Adjust this if the prompt is different
    child.expect(['\$', '#', '>'], timeout=30)
    print("Logged in!")

    print(f"Sending server command: {SERVER_CMD}")
    child.sendline(SERVER_CMD)
    
    # We want to keep this running and stream output
    # But since we need to run the client locally, we might just leave this running for a bit
    # verifying it started
    
    try:
        # Expect "Server listening..." or errors (using regex for ImportError to capture message)
        # Note: We use raw string for regex
        index = child.expect(["Server listening on port 5555", r"Traceback \(most recent call last\):", r"ImportError: .*"], timeout=300)
        
        if index == 0:
            print("Server started successfully and listening!")
            # Keep process alive for testing
            print("Keeping connection open for 60 seconds...")
            time.sleep(60)
        else:
            print(f"Error detected! Matched index {index}")
            print("--- BEFORE match ---")
            print(child.before)
            print("--- AFTER match ---")
            print(child.after)
            print("--- REMAINING ---")
            print(child.read())
            sys.exit(1)
        
    except pexpect.TIMEOUT:
        print("Timeout waiting for server start message.")
        print(child.before)
    except pexpect.EOF:
        print("Process/Connection ended unexpectedly.")
        print(child.before)
    finally:
        child.close()

if __name__ == "__main__":
    main()
