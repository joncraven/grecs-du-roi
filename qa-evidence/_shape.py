import subprocess, sys
font = sys.argv[1]
text = sys.argv[2]
out = sys.argv[3]
sz = sys.argv[4] if len(sys.argv) > 4 else "96"
subprocess.check_call(["hb-view", "--font-size", sz, "--margin", "24", "-o", out, font, text])
print("wrote", out)
