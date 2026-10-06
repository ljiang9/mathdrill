#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mathdrill —— 口算练习小游戏。

随机出 10 道（可配置）四则运算题，计时、记分、统计正确率。
"""
from __future__ import annotations

import argparse
import random
import sys
import time

OPS_LABEL = {"+": "＋", "-": "－", "×": "×", "÷": "÷"}
# 方便从命令行输入的别名
OPS_ALIAS = {"x": "×", "X": "×", "*": "×", "/": "÷", ":": "÷"}

_KIDS_FRIENDLY = True  # 减法默认不出现负数答案


def normalize_ops(raw: str) -> list[str]:
    """把 --ops 字符串归一化为标准运算符列表。"""
    ops = []
    for ch in raw:
        ch = OPS_ALIAS.get(ch, ch)
        if ch in OPS_LABEL and ch not in ops:
            ops.append(ch)
    return ops


def gen_question(ops: list[str], digits: int, rng: random.Random) -> tuple[str, int]:
    """生成一道题，返回 (题面字符串, 正确答案)。"""
    op = rng.choice(ops)
    lo, hi = 10 ** (digits - 1), 10 ** digits - 1
    if digits == 1:
        lo = 0
    if op == "+":
        a = rng.randint(lo, hi)
        b = rng.randint(lo, hi)
        return f"{a} ＋ {b} ＝ ?", a + b
    if op == "-":
        a = rng.randint(lo, hi)
        b = rng.randint(lo, hi)
        if _KIDS_FRIENDLY and a < b:  # 让小朋友不算负数
            a, b = b, a
        return f"{a} － {b} ＝ ?", a - b
    if op == "×":
        a = rng.randint(lo, hi)
        b = rng.randint(lo, hi)
        return f"{a} × {b} ＝ ?", a * b
    # 除法：先定除数和商，保证整除
    b = rng.randint(max(lo, 1), hi)
    ans = rng.randint(max(lo, 1), hi)
    a = b * ans
    return f"{a} ÷ {b} ＝ ?", ans


def check(answer_text: str, correct: int) -> tuple[bool, str]:
    """解析用户输入。返回 (是否正确, 提示信息)。"""
    s = answer_text.strip().replace("，", ",")
    try:
        v = int(s, 10)
    except ValueError:
        return False, "⚠ 请输入整数（直接输入数字即可），这题记为错误。"
    return (v == correct, "✔ 答对了！" if v == correct else f"✘ 答错了，正确答案是 {correct}。")


def run_quiz(args, input_fn=None, print_fn=None, rng=None) -> dict:
    input_fn = input_fn or input
    print_fn = print_fn or print
    rng = rng or random.Random()
    ops = normalize_ops(str(args.ops))
    if not ops:
        raise SystemExit("错误：--ops 里至少要包含一个有效运算符（+ - × ÷，也可用 x / 做别名）")

    print_fn(f"\n🧮 口算挑战：共 {args.count} 题（运算符：{''.join(OPS_LABEL[o] for o in ops)}，{args.digits} 位数）")
    print_fn("提示：除法都是整除的，减法不会出现负数。输入整数答案后回车，开始！\n")

    score = 0
    wrong: list[tuple[str, int, str]] = []
    start = time.perf_counter()
    for i in range(1, args.count + 1):
        q, ans = gen_question(ops, args.digits, rng)
        print_fn(f"第 {i}/{args.count} 题：{q}")
        try:
            user = input_fn("你的答案：")
        except (EOFError, KeyboardInterrupt):
            print_fn("\n\n⏹ 已提前结束。")
            break
        ok, msg = check(user, ans)
        print_fn(msg)
        if ok:
            score += 1
        else:
            wrong.append((q, ans, user.strip()))
    elapsed = time.perf_counter() - start

    answered = score + len(wrong)
    accuracy = (score / answered * 100) if answered else 0.0
    print_fn("\n" + "=" * 32)
    print_fn(f"🏁 成绩：答对 {score}/{answered} 题，正确率 {accuracy:.1f}%，用时 {elapsed:.1f} 秒")
    if answered:
        print_fn(f"⏱ 平均每题 {elapsed / answered:.1f} 秒")
    if wrong:
        print_fn("\n错题回顾：")
        for q, ans, user in wrong:
            print_fn(f"  {q} 正确答案 {ans}（你填了：{user or '（空）'}）")
    grade = "🌟 口算小达人！" if accuracy >= 90 else "💪 继续加油！"
    print_fn(f"\n{grade}")
    return {"score": score, "answered": answered, "accuracy": accuracy, "elapsed": elapsed}


def auto_demo(args, print_fn=None):
    """--auto：脚本化演示，自动作答（奇数题答对、偶数题答错），用于测试。"""
    print_fn = print_fn or print
    rng = random.Random(42)

    planned = [gen_question(normalize_ops(str(args.ops)), args.digits, rng)
               for _ in range(args.count)]

    def fake_input(prompt=""):
        q, ans = planned[fake_input.i]
        fake_input.i += 1
        val = ans if fake_input.i % 2 == 1 else ans + 1  # 奇数题对、偶数题错
        print_fn(prompt + str(val))
        return str(val)

    fake_input.i = 0
    return run_quiz(args, input_fn=fake_input, print_fn=print_fn, rng=random.Random(42))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="mathdrill —— 口算练习小游戏")
    p.add_argument("--ops", default="+-×÷", help="运算符选择，如 '+-'（默认: +-×÷）")
    p.add_argument("--digits", type=int, default=1, choices=[1, 2, 3], help="数字位数（默认: 1）")
    p.add_argument("--count", type=int, default=10, help="题目数量（默认: 10）")
    p.add_argument("--auto", action="store_true", help="自动演示模式（无需人工输入）")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.count < 1:
        print("错误：--count 至少为 1", file=sys.stderr)
        return 2
    if args.auto:
        run_quiz_args = args
        result = auto_demo(run_quiz_args)
    else:
        result = run_quiz(args)
    return 0 if result["answered"] else 1


if __name__ == "__main__":
    sys.exit(main())
