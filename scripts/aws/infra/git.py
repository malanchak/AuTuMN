import subprocess as sp


def get_commit_hash():
    return run_cmd(["git rev-parse HEAD"])


def get_branch():
    return run_cmd(["git rev-parse --abbrev-ref HEAD"])


def set_new_branch(branch_name):
    run_cmd([f"git checkout -b {branch_name}"])


def set_branch(branch_name):
    run_cmd([f"git checkout {branch_name}"])


def push_new_branch(branch_name):
    run_cmd([f"git push -u origin {branch_name}"])


def run_cmd(cmd):
    proc = sp.run(cmd, shell=True, check=True, stdout=sp.PIPE, stderr=sp.PIPE encoding="utf-8")
    return proc.stdout.strip(), proc.stderr.strip()
