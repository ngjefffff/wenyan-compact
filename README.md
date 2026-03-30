# wenyan-compact

**Cognitive state relay for Claude Code. Encodes session state in Classical Chinese — semantic weight the model pre-activates directly, without reconstruction.**

A Claude Code skill that compresses conversation state into Classical Chinese (文言文) snapshots — pre-filling the next session’s context so the AI picks up exactly where you left off, without re-derivation.

---

## The Problem

Every Claude session starts blank. Without a relay:

- You re-explain architecture decisions made three sessions ago
- Claude re-proposes options you already closed
- Reasoning momentum resets. Every session starts from zero

Existing “memory” solutions store what was *said* — summaries, RAG chunks, conversation logs. The model reads them and reconstructs. There is always a gap between what was stored and what gets activated.

This works differently. Cognitive state is encoded in Classical Chinese and loaded directly into context. The model does not reconstruct it — it pre-activates the semantic weight already embedded in the tokens.

---

## What is Classical Chinese (Wenyan)?

Classical Chinese (文言文, *wényán*) is the literary written form of Chinese used from roughly 500 BC through the early 20th century — the Latin of East Asia. A standardized written language that outlasted spoken dialects by millennia.

Unlike modern languages, wenyan contains no filler words — no articles, no tense markers, no helper verbs. Every character carries full semantic weight. A proposition that takes a full sentence in English or modern Chinese takes 4–8 characters in wenyan.

**The key fact for AI users:** Modern LLMs were trained on massive corpora that include classical Chinese texts — Confucius, Sun Tzu, Tang dynasty records, 2500 years of literature. Wenyan is not foreign to the model. It pre-activates existing semantic structures directly, without translation or reconstruction overhead.

This was independently confirmed in peer-reviewed research (CC-BOS, ICLR 2026): classical Chinese can *“partially bypass existing safety constraints”* precisely *“owing to its conciseness and obscurity”* — evidence that models process wenyan at a deep semantic level, not surface pattern-matching.

---

## How It Works

Two layers. One persistent. One per session.

```
冊 (cè)   — session snapshot. One file per session. Full record, never compressed.
经 (jīng) — distilled global state. Updated after each session. Pre-loaded on start.
```

The **冊** captures the cognitive trace of one session: decisions made, paths closed, new knowledge, where thinking is pointed next.

The **经** distills the big picture across sessions: direction, definitions, key decisions. This is what pre-fills your context window when a new session starts — not as text to parse, but as semantic weight to activate.

A `SessionStart` hook (installed by `init.py`) loads both automatically — before you type your first message.

### What a 冊 entry looks like

```
弃微服务，取单体。∵运维弱，故障恢复超限。
续：建 Schema Registry + Entity Manager。
疑：认知升级引擎合并协议未定。
```

Translation:
```
Rejected microservices, chose monolith. Because: weak ops, recovery time exceeds limits.
Next: build Schema Registry + Entity Manager.
Open: Cognitive Upgrade Engine merge protocol undefined.
```

Each entry is a self-contained semantic unit. The next instance loads it and activates — not reads and summarizes.

---

## Compression Evidence

Source: CC-BOS abstract (Huang et al., ICLR 2026). Token counts verified with `tiktoken cl100k_base`.

**Original English** (237 tokens):
> As Large Language Models (LLMs) are increasingly used, their security risks have drawn increasing attention. Existing research reveals that LLMs are highly susceptible to jailbreak attacks, with effectiveness varying across language contexts. This paper investigates the role of classical Chinese in jailbreak attacks. Owing to its conciseness and obscurity, classical Chinese can partially bypass existing safety constraints, exposing notable vulnerabilities in LLMs. Based on this observation, this paper proposes a framework, CC-BOS, for the automatic generation of classical Chinese adversarial prompts based on multi-dimensional fruit fly optimization, facilitating efficient and automated jailbreak attacks in black-box settings. Prompts are encoded into eight policy dimensions — covering role, behavior, mechanism, metaphor, expression, knowledge, trigger pattern and context; and iteratively refined via smell search, visual search, and cauchy mutation. This design enables efficient exploration of the search space, thereby enhancing the effectiveness of black-box jailbreak attacks. To enhance readability and evaluation accuracy, we further design a classical Chinese to English translation module. Extensive experiments demonstrate that effectiveness of the proposed CC-BOS, consistently outperforming state-of-the-art jailbreak attack methods.

**Modern Chinese** (417 tokens):
> 随着大型语言模型的广泛应用，其安全风险日益受到关注。现有研究表明，大型语言模型极易受到越狱攻击，且攻击效果因语言环境而异。本文研究了文言文在越狱攻击中的作用。由于文言文的简洁性和晦涩性，它能够部分绕过现有的安全约束，暴露出大型语言模型中显著的安全漏洞。基于这一观察，本文提出了一个框架CC-BOS，用于基于多维果蝇优化自动生成文言文对抗性提示，在黑盒设置中实现高效自动化的越狱攻击。提示被编码为八个策略维度，涵盖角色、行为、机制、隐嗻、表达、知识、触发模式和上下文，并通过嗅觉搜索、视觉搜索和柯西变异进行迭代优化。这种设计能够高效探索搜索空间，从而提高黑盒越狱攻击的效果。为了提高可读性和评估准确性，我们进一步设计了文言文到英文的翻译模块。大量实验证明了所提CC-BOS的有效性，始终优于最先进的越狱攻击方法。

**Wenyan compressed** (186 tokens):
> 大型语言模型越狱风险渐显，效果因语境而异。文言简洁晦涩，能绕部分安全约束，暴模型漏洞。∴提CC-BOS框架：以果蝇多维优化自动生文言对抗提示，攻黑笱模型。提示分八维（角色、行为、机制、隐嗻、表达、知识、触发、语境），经嗅搜、视搜、柯西变异迭代精化。附文言转英文模块提可读性。实验证CC-BOS优于现有越狱方法。

| | Tokens | vs Wenyan |
|---|---|---|
| English | 237 | 1.27x |
| Modern Chinese | 417 | 2.24x |
| **Wenyan** | **186** | **—** |

**vs Modern Chinese:** 2.24x token compression — same semantic content, less than half the context cost.

**vs English:** The token ratio is modest (1.27x). The structural difference is not in count but in kind: an English summary is narrative the model must interpret. A wenyan 冊 is semantic weight the model pre-activates — decisions, directions, open tensions encoded in a form already native to the model’s weight space.

> `cl100k_base` tokenizes Chinese characters at ~1.5 tokens/character vs ~0.7 tokens/word for English. Claude’s native tokenizer may yield different ratios; the Chinese → wenyan advantage holds regardless.

---

## Install

```bash
# 1. Copy the skill to your Claude Code skills directory
cp -r wenyan-session-compact ~/.claude/skills/

# 2. Run init in your project
cd your-project
python ~/.claude/skills/wenyan-session-compact/scripts/init.py
```

`init.py` will:
- Create `.wy-session/` at your project root (经 + 冊 storage)
- Add `.wy-session/` to `.gitignore`
- Inject `SessionStart` and `PreCompact` hooks into `.claude/settings.json`

Restart Claude Code. From the next session, context loads automatically.

---

## Usage

**At session end**, trigger the skill:

```
/session-manager
```

Claude will write the 冊 (session snapshot in wenyan), then distill new decisions into the 经 (global state). Next session, everything is pre-loaded.

**First time only**, fill in the `## 道` section of `.wy-session/global-state.md` with your project’s core direction. This is your first 经 entry.

---

## The Bigger Picture

Wenyan is the first instantiation of a broader principle: **find the compression medium with the highest semantic weight per token that the model already knows**.

Classical Chinese is optimal for the current generation of LLMs because of their training data. Future candidates — Sanskrit’s verb-dense structure, formal logic notation, other classical written languages — follow the same logic. As training data evolves, the optimal medium may shift.

The pattern is the point: context is first-class. The AI is a visitor. The model persists across sessions. The AI does not.

---

## Reference

CC-BOS: *“Obscure but Effective: Classical Chinese Jailbreak Prompt Optimization via Bio-Inspired Search”*
Huang et al., ICLR 2026. [arXiv:2602.22983](https://arxiv.org/abs/2602.22983)

> *“Owing to its conciseness and obscurity, classical Chinese can partially bypass existing safety constraints, exposing notable vulnerabilities in LLMs.”*

---

## License

CC BY-NC 4.0 — free to use, not for commercial gain. © 2026 Ng Jeff
