# TI-BASIC Program Communication and Encoding Protocol

## Table of Contents

1. [Overview and Significance](#1-overview-and-significance)  
   1.1. [Communication Model](#11-communication-model)  
   1.2. [Protocol Overview](#12-protocol-overview)  
2. [TI-BASIC Text Encoding](#2-ti-basic-text-encoding)  
   2.1. [Character Encoding Structure](#21-character-encoding-structure)  
   2.2. [Single-Byte Characters](#22-single-byte-characters)  
   2.3. [Multi-Byte Characters](#23-multi-byte-characters)  
   2.4. [TI's Non-Standard Length Encoding](#24-tis-non-standard-length-encoding)  
3. [Reading TI-BASIC Programs](#3-reading-ti-basic-programs)  
   3.1. [Communication Flow](#31-communication-flow)  
   3.2. [Program Content Transfer Format](#32-program-content-transfer-format)  
   3.3. [Title-Based Dynamic Fields](#33-title-based-dynamic-fields)  
   3.4. [Complete Example: Reading Program "HELLO"](#34-complete-example-reading-program-hello)  
4. [Writing TI-BASIC Programs](#4-writing-ti-basic-programs)  
   4.1. [Communication Flow](#41-communication-flow)  
   4.2. [Dynamic Field Calculations](#42-dynamic-field-calculations)  
   4.3. [Complete Example: Writing Program "HELLO"](#43-complete-example-writing-program-hello)  
5. [Replacing TI-BASIC Programs](#5-replacing-ti-basic-programs)  
   5.1. [Communication Flow](#51-communication-flow)  
   5.2. [Title Collision Detection](#52-title-collision-detection)  
   5.3. [Program Content Modification](#53-program-content-modification)  
   5.4. [The Importance of Collision Detection](#54-the-importance-of-collision-detection)  
6. [Implementation Guidelines](#6-implementation-guidelines)  
   6.1. [Best Practices](#61-best-practices)  
   6.2. [Common Pitfalls](#62-common-pitfalls)  
7. [Appendices](#7-appendices)  
   7.1. [Complete Character Encoding Reference](#71-complete-character-encoding-reference)  
   7.2. [Quick Reference Guide](#72-quick-reference-guide)  

---

## 1. Overview and Significance

At first glance, TI-BASIC programs may seem like a niche format with limited utility. However, they serve as the foundation for establishing **reliable communication between a host device and the TI-84 Plus CE calculator**.

### 1.1. Communication Model

The primary objective is to create a **structured messaging system** that enables bidirectional data transfer. To understand this approach, consider the familiar email model, which consists of four essential components:

1. **Sender** (author)  
2. **Receiver** (recipient)  
3. **Subject** line  
4. **Message body**  

A TI-BASIC program naturally maps to this communication model:

| Email Component | TI-BASIC Equivalent |
|-----------------|---------------------|
| Sender          | Host Device         |
| Receiver        | TI-84 Plus CE       |
| Subject         | Program Title       |
| Body            | Program Content     |

This structural alignment makes TI-BASIC programs an ideal medium for encoding and transferring messages. The program title serves as a subject identifier, while the program content carries the actual data payload.

**Key Benefits:**
- Familiar interface for users already comfortable with TI-BASIC
- Structured format that prevents data corruption
- Native support for the calculator's [character encoding system](#2-ti-basic-text-encoding)

### 1.2. Protocol Overview

The communication protocol supports three fundamental operations, each with increasing complexity:

#### Operation Types

1. **READ** - Retrieve existing programs from calculator
   - **Steps:** 6-step handshake
   - **Complexity:** Low (calculator-driven responses)
   - **Use Case:** Data retrieval, backup operations

2. **WRITE** - Create new programs on calculator  
   - **Steps:** 12-step handshake
   - **Complexity:** Medium (validation and content transfer)
   - **Use Case:** Program deployment, data transmission

3. **REPLACE** - Overwrite existing programs
   - **Steps:** 18-step handshake (includes collision detection)
   - **Complexity:** High (safety mechanisms and user confirmation)
   - **Use Case:** Program updates, data synchronization

#### Communication Characteristics

All operations follow a **host-initiated, acknowledgment-driven pattern**:
- Host device controls transaction flow
- Calculator responds with structured acknowledgments
- Each data packet requires confirmation before proceeding
- Collision detection provides safety mechanisms for data protection

#### What You'll Learn

This documentation will guide you through:
- The [proprietary text encoding system](#2-ti-basic-text-encoding) used by Texas Instruments
- Detailed packet structures and field calculations for each operation
- Complete implementation examples with real hex data
- Best practices for robust protocol implementation
- Common pitfalls and how to avoid them

---

## 2. TI-BASIC Text Encoding

Communication with the TI-84 Plus CE uses a **vendor-specific USB bulk protocol** that transmits raw binary data. This requires precise byte-level encoding and decoding to ensure data integrity.

Texas Instruments does not use standard encoding formats like ASCII or UTF-8. Instead, they implement a **proprietary character encoding** that maps TI-BASIC characters and symbols to specific byte sequences.

Understanding this encoding is essential for:
- Parsing raw TI-BASIC program data  
- Constructing valid program payloads for transmission  
- Interpreting incoming calculator data correctly

### 2.1. Character Encoding Structure

The TI-BASIC encoding uses either **one or two bytes** per character, depending on the character type. This hybrid approach allows representation of both standard text and calculator-specific symbols.

### 2.2. Single-Byte Characters

**Uppercase Letters (A-Z):**
Standard ASCII encoding from `0x41` to `0x5A`.

| Character | Hex Code | Character | Hex Code | Character | Hex Code |
|-----------|----------|-----------|----------|-----------|----------|
| A         | `41`     | J         | `4A`     | S         | `53`     |
| E         | `45`     | K         | `4B`     | T         | `54`     |
| H         | `48`     | O         | `4F`     | Z         | `5A`     |

**Digits (0-9):**
Standard ASCII encoding from `0x30` to `0x39`.

| Character | Hex Code | Character | Hex Code |
|-----------|----------|-----------|----------|
| 0         | `30`     | 5         | `35`     |
| 3         | `33`     | 9         | `39`     |

**Essential Symbols:**
Single-byte values for basic punctuation and operators.

| Symbol    | Hex Code | Description | Symbol    | Hex Code | Description |
|-----------|----------|-------------|-----------|----------|-------------|
| Space     | `29`     | Whitespace  | `.`       | `3A`     | Period      |
| Newline   | `3F`     | Line break  | `(`       | `10`     | Left paren  |
| `)`       | `11`     | Right paren | `+`       | `70`     | Addition    |
| `-`       | `71`     | Subtraction | `=`       | `6A`     | Equals      |

### 2.3. Multi-Byte Characters

**Lowercase Letters (a-z):**
Two-byte sequences with various prefixes (`0x62`, `0xBB`, or `0x5E`).

| Character | Hex Bytes | Character | Hex Bytes | Character | Hex Bytes |
|-----------|-----------|-----------|-----------|-----------|-----------|
| a         | `62 16`   | n         | `62 02`   | u         | `5E 80`   |
| e         | `62 1A`   | o         | `BB BF`   | x         | `BB C8`   |
| k         | `BB BA`   | q         | `BB C1`   | z         | `62 23`   |

**Extended Symbols:**
Special characters using the `0xBB` prefix.

| Symbol | Hex Bytes | Description | Symbol | Hex Bytes | Description |
|--------|-----------|-------------|--------|-----------|-------------|
| `@`    | `BB D1`   | At symbol   | `#`    | `BB D2`   | Hash/pound  |
| `&`    | `BB D4`   | Ampersand   | `_`    | `BB D9`   | Underscore  |
| `\`    | `BB D7`   | Backslash   | `|`    | `BB D8`   | Pipe        |

*For complete character mappings, see [Appendix 7.1](#71-complete-character-encoding-reference).*

### 2.4. TI's Non-Standard Length Encoding

Many protocol operations require length fields that use TI's proprietary encoding system. The **CCCC** field in packet structures uses an unusual byte arrangement that differs from standard little-endian or big-endian formats:

**For lengths ≤ 255 bytes:**
- Byte 1: Length value
- Byte 2: `00`
- Example: 120 bytes → `78 00`

**For lengths > 255 bytes:**
- Byte 1: Least significant byte  
- Byte 2: Most significant byte
- Example: 1000 bytes (0x03E8) → `E8 03`

This encoding pattern appears throughout the protocol and must be implemented correctly for successful communication.

---

## 3. Reading TI-BASIC Programs

Reading a program from the TI-84 Plus CE is the simplest communication operation. The host initiates the request and drives the entire transaction through a **predictable six-step sequence**.

### 3.1. Communication Flow

| Step | Direction | Description                          |
|------|-----------|--------------------------------------|
| 1    | OUT       | Host sends read request with title   |
| 2    | IN        | Calculator acknowledges request      |
| 3    | IN        | Calculator confirms program exists   |
| 4    | OUT       | Host acknowledges confirmation       |
| 5    | IN        | Calculator sends program content     |
| 6    | OUT       | Host sends final acknowledgment      |

### 3.2. Program Content Transfer Format

Step 5 uses a specialized packet structure for transferring the actual program content:

**Format:** `AAAAAAAA-04-BBBBBBBB-000D-CCCC-D`

**Field Definitions:**
- **D**: TI-BASIC program content (encoded per [Section 2](#2-ti-basic-text-encoding))
- **AAAAAAAA**: Total packet size = `6 + len(D)` (8-digit hex, zero-padded)
- **BBBBBBBB**: Secondary size = `2 + len(D)` (8-digit hex, zero-padded)  
- **CCCC**: Content length using [TI's non-standard encoding](#24-tis-non-standard-length-encoding)

### 3.3. Title-Based Dynamic Fields

Program titles use uppercase ASCII letters and digits (up to 8 characters). The encoding process involves generating several Dynamic Packet Signatures (DPS) — deterministic, operation-specific values derived from metadata like the program title length. While not traditional checksums, these signatures serve as structural markers used to align and validate packet composition across different phases of the protocol.

| Field            | Calculation                            | Example ("HELLO") |
|------------------|----------------------------------------|-------------------|
| **Title**        | Title as ASCII bytes                   | `48 45 4C 4C 4F`  |
| **Title length** | Title length (4-digit hex)| `0005`            |
| **DPS 1**   | `40 + title_length` (8-digit hex)      | `0000002D`        |
| **DPS 2**   | `34 + title_length` (8-digit hex)      | `00000027`        |
| **DPS 3**   | `50 + title_length` (8-digit hex)      | `00000037`        |
| **DPS 4**   | `44 + title_length` (8-digit hex)      | `00000031`        |

### 3.4. Complete Example: Reading Program "HELLO"

**Step 1: Request to read program "HELLO"**
Host → Calculator (Using Title, Length, DPS 1 and 2)
```
0000002D|04|00000027|000C|0005|48454C4C4F|00017FFFFFFF0006000100020003000500080041000100110004F00F00050000
```

**Step 2: Request acknowledged**
Calculator → Host
```
0000000205E000
```

**Step 3: Program "HELLO" existence confirmed**
Calculator → Host (Using Title, Title length, DPS 3 and 4)
```
00000037|04|00000031|000A|0005|48454C4C4F|0000060001000004000000100002000004F0070005000300000100000501000800000400000000004101
```

**Step 4: Acknowledged**
Host → Calculator
```
0000000205E000
```

**Step 5: Program content**
Calculator → Host
```
Encoded using Program Content Transfer Format (Section 3.2)
```

**Step 6: Final acknowledgment - end transaction**
Host → Calculator
```
0000000205E000
```

---

## 4. Writing TI-BASIC Programs

Writing programs to the calculator involves a more complex **twelve-step handshake** that includes validation checks and content transfer. The host initiates and controls the entire process.

### 4.1. Communication Flow

| Step | Direction | Description                           |
|------|-----------|---------------------------------------|
| 1    | OUT       | Host sends write request with title   |
| 2    | IN        | Calculator acknowledges request       |
| 3    | IN        | Calculator indicates ready to write   |
| 4    | OUT       | Host acknowledges ready status        |
| 5    | IN        | Calculator confirms title is available, continue|
| 6    | OUT       | Host acknowledges availability        |
| 7    | OUT       | Host sends program content            |
| 8    | IN        | Calculator acknowledges content       |
| 9    | IN        | Calculator signals write completion   |
| 10   | OUT       | Host acknowledges completion          |
| 11   | OUT       | Host sends end transmission signal    |
| 12   | IN        | Calculator sends final acknowledgment |

### 4.2. Dynamic Field Calculations

Write operations partially use the field calculations of [read operations](#33-title-based-dynamic-fields):

| Field            | Calculation                                    | Example ("HELLO") |
|------------------|------------------------------------------------|-------------------|
| **Title**        | Title as ASCII bytes                           | `48 45 4C 4C 4F`  |
| **Title length** | Title length (4-digit hex)        | `0005`            |
| **DPS 1**   | `50 + title_length` (8-digit hex)              | `00000037`        |
| **DPS 2**   | `44 + title_length` (8-digit hex)              | `00000031`        |

### 4.3. Complete Example: Writing Program "HELLO"

**Step 1: Request to write program "HELLO"**
Host → Calculator (Using Title, Title length, DPS 1 and 2)
```
00000037|04|00000031|000B|0005|48454C4C4F|0000000004000005000100040000000400020004F00B0005000300010000410001000008000400000000
```

**Step 2: Write request acknowledged**
Calculator → Host
```
0000000205E000
```

**Step 3: Ready to write**
Calculator → Host
```
0000000A0400000004BB0000075300
```

**Step 4: Acknowledged**
Host → Calculator
```
0000000205E000
```

**Step 5: Title available, send program content**
Calculator → Host
```
000000070400000001AA0001
```

**Step 6: Acknowledged, sending content**
Host → Calculator
```
0000000205E000
```

**Step 7: Program Content**
Host → Calculator
```
Encoded using Program Content Transfer Format (Section 3.2)
```

**Step 8: Acknowledged, starting writing operation**
Calculator → Host
```
0000000205E000
```

**Step 9: Writing Complete**
Calculator → Host
```
000000070400000001AA0001
```

**Step 10: Acknowledged**
Host → Calculator
```
0000000205E000
```

**Step 11: End Transmission**
Host → Calculator
```
000000060400000000DD00
```

**Step 12: Acknowledged ending Transmission**
Calculator → Host
```
0000000205E000
```

---

## 5. Replacing TI-BASIC Programs

Replacing existing programs begins with the same [write sequence](#4-writing-ti-basic-programs), but when the calculator detects a title collision in Step 5, it responds differently. The host then restarts the write sequence using the **modified overwrite flag** in the write request packet.

The replacement process involves:
1. **Initial write attempt** following the standard [write sequence](#4-writing-ti-basic-programs)
2. **Collision detection** when the calculator finds an existing program with the same title  
3. **Restart with overwrite flag** - the write sequence begins again with a modified overwrite flag, resulting in a single byte difference between a write sequence and an overwrite sequence

### 5.1. Communication Flow

The replace operation follows this 18-step pattern:

| Step | Direction | Description                                     |
|------|-----------|-------------------------------------------------|
| 1    | OUT       | Host sends write request with title             |
| 2    | IN        | Calculator acknowledges request                 |
| 3    | IN        | Calculator indicates ready to write             |
| 4    | OUT       | Host acknowledges ready status                  |
| 5    | IN        | Calculator detects existing program, requests overwrite |
| 6    | OUT       | Host acknowledgment                             |
| 7    | OUT       | Host requests overwrite, sequence restarts (overwrite flag = `01`) |
| 8    | IN        | Calculator acknowledges request                 |
| 9    | IN        | Calculator indicates ready to write             |
| 10   | OUT       | Host acknowledges ready status                  |
| 11   | IN        | Calculator signals continue                     |
| 12   | OUT       | Host acknowledgment                             |
| 13   | OUT       | Host sends program content                      |
| 14   | IN        | Calculator acknowledges content                 |
| 15   | IN        | Calculator signals write completion             |
| 16   | OUT       | Host acknowledges completion                    |
| 17   | OUT       | Host sends end transmission signal              |
| 18   | IN        | Calculator sends final acknowledgment           |

### 5.2. Title Collision Detection

When a program with the specified title already exists, Step 5 returns:

**Step 5: Title Exists (Ready to Overwrite)**
```
000000080400000002EE000012
```

This response indicates the calculator has detected a collision and requests the host send a new sequence with an overwrite flag.

### 5.3. Program Content Modification

From step 7 onwards, the host sends practically the same sequence as a [write sequence](#4-writing-ti-basic-programs). The only structural difference is **one byte** in the first step:

**New Program (Write):**
```
DPS 1|04|DPS 2|000B|Title length|Title|000000001800...
```

**Existing Program (Replace):**
```
DPS 1|04|DPS 2|000B|Title length|Title|000000001801...
```

A single byte changes from `00` to `01` to signal an overwrite operation. This change is located 5 bytes after the Title of the write request packet.

**Collision Detection:**
The calculator's response in Step 5 determines the operation mode:
- `000000070400000001AA0001`: New program (proceed with write)
- `000000080400000002EE000012`: Existing program (retry with overwrite flag)

### 5.4. The Importance of Collision Detection

The overwrite sequence essentially restarts completely after step 6, which may appear inefficient. However, this design serves a crucial purpose in user safety and system reliability.

**Purpose of the Initial Detection Phase:**

1. **User Confirmation**: The first 6 steps provide the host application with definitive knowledge that a program with the target title already exists. This creates an opportunity for the host to present the user with a clear choice: "Program 'HELLO' already exists. Do you want to overwrite it?"

2. **Graceful Abort**: If the user chooses not to overwrite, the transaction can be terminated cleanly without any system-level modifications or data corruption.

3. **Safety Mechanism**: This two-phase approach prevents accidental overwrites in automated systems where user programs might contain important work or data.

4. **Error Prevention**: For non-technical users or batch operations, this collision detection provides a critical safety net against unintentional data loss.

While the protocol could theoretically support direct overwrites, the deliberate design choice to require explicit confirmation reflects Texas Instruments' commitment to data safety. In educational environments where calculators are shared and student work is valuable, this extra step prevents the frustration and potential academic consequences of accidentally deleted programs.

**Implementation Recommendation:**
When implementing this protocol, always respect the collision detection phase and provide clear user feedback. Consider implementing features like program backup or version control to further protect user data during overwrite operations.

---

## 6. Implementation Guidelines

### 6.1. Best Practices

1. **Always validate encoding**: Ensure proper [character encoding](#2-ti-basic-text-encoding) before transmission using the reference tables in [Appendix 7.1](#71-complete-character-encoding-reference)

2. **Handle length calculations carefully**: Pay special attention to the [non-standard CCCC field](#24-tis-non-standard-length-encoding) - this is the most common source of implementation errors

3. **Implement proper acknowledgments**: Each data packet requires appropriate responses. Missing ACK packets will cause the calculator to timeout and abort the transaction

4. **Timeout handling**: Implement reasonable timeouts (2-5 seconds) for USB operations to handle calculator disconnections gracefully

5. **Respect collision detection**: Always implement the [safety mechanisms](#54-the-importance-of-collision-detection) for program replacement - never bypass the collision detection phase

6. **Test with edge cases**: Verify your implementation works with:
   - Single-character program names
   - Maximum length program names (8 characters)
   - Programs containing special characters
   - Empty programs
   - Large programs (>1KB)

### 6.2. Common Pitfalls

**Critical Implementation Errors:**

- **Incorrect CCCC encoding**: The reversed byte order for lengths > 255 bytes. Always use least significant byte first for multi-byte lengths

- **Missing acknowledgments**: Skipping ACK packets (`0000000205E000`) causes communication failure. Every IN packet must be acknowledged

- **Character encoding errors**: Using standard ASCII encoding for lowercase letters instead of the [multi-byte sequences](#23-multi-byte-characters)

- **Field calculation mistakes**: Off-by-one errors in [dynamic field computation](#33-title-based-dynamic-fields). Verify DPS calculations against the reference formulas

- **Ignoring collision detection**: Bypassing the safety mechanisms in [program replacement](#5-replacing-ti-basic-programs) can lead to unintentional data loss

**Debug Recommendations:**

- Log all USB traffic in hex format for analysis
- Verify packet lengths match their declared sizes
- Test each operation type independently before combining them
- Use known working programs as test cases
- Implement verbose error reporting for protocol violations

---

## 7. Appendices

### 7.1. Complete Character Encoding Reference

#### Lowercase Letters

| Char | Encoding | Char | Encoding | Char | Encoding | Char | Encoding |
|------|----------|------|----------|------|----------|------|----------|
| a    | `62 16`  | b    | `62 17`  | c    | `62 18`  | d    | `62 19`  |
| e    | `62 1A`  | f    | `BB B5`  | g    | `BB B6`  | h    | `BB B7`  |
| i    | `BB B8`  | j    | `BB B9`  | k    | `BB BA`  | l    | `BB BC`  |
| m    | `BB BD`  | n    | `62 02`  | o    | `BB BF`  | p    | `62 22`  |
| q    | `BB C1`  | r    | `62 12`  | s    | `62 34`  | t    | `62 24`  |
| u    | `5E 80`  | v    | `5E 81`  | w    | `5E 82`  | x    | `BB C8`  |
| y    | `BB C9`  | z    | `62 23`  |      |          |      |          |

#### Uppercase Letters

| Char | Encoding | Char | Encoding | Char | Encoding | Char | Encoding |
|------|----------|------|----------|------|----------|------|----------|
| A    | `41`     | B    | `42`     | C    | `43`     | D    | `44`     |
| E    | `45`     | F    | `46`     | G    | `47`     | H    | `48`     |
| I    | `49`     | J    | `4A`     | K    | `4B`     | L    | `4C`     |
| M    | `4D`     | N    | `4E`     | O    | `4F`     | P    | `50`     |
| Q    | `51`     | R    | `52`     | S    | `53`     | T    | `54`     |
| U    | `55`     | V    | `56`     | W    | `57`     | X    | `58`     |
| Y    | `59`     | Z    | `5A`     |      |          |      |          |

#### Numbers and Symbols

| Char | Encoding | Char | Encoding | Char | Encoding | Char | Encoding |
|------|----------|------|----------|------|----------|------|----------|
| 0    | `30`     | 1    | `31`     | 2    | `32`     | 3    | `33`     |
| 4    | `34`     | 5    | `35`     | 6    | `36`     | 7    | `37`     |
| 8    | `38`     | 9    | `39`     | Space| `29`     | \n   | `3F`     |
| .    | `3A`     | ,    | `2B`     | :    | `3E`     | ;    | `BB`     |
| !    | `2D`     | ?    | `AF`     | '    | `AE`     | "    | `2A`     |
| (    | `10`     | )    | `11`     | [    | `06`     | ]    | `07`     |
| {    | `08`     | }    | `09`     | +    | `70`     | -    | `71`     |
| *    | `82`     | /    | `83`     | =    | `6A`     | <    | `6B`     |
| >    | `6C`     | ^    | `F0`     | `    | `BB D5`  | ~    | `BB CF`  |
| @    | `BB D1`  | #    | `BB D2`  | $    | `BB D3`  | %    | `BB DA`  |
| &    | `BB D4`  | _    | `BB D9`  | \\   | `BB D7`  | \|   | `BB D8`  |

### 7.2. Quick Reference Guide

#### Operation Summary

| Operation | Steps | Key Characteristics | Primary Use Case |
|-----------|-------|---------------------|------------------|
| READ      | 6     | Simple, calculator-driven responses | Data retrieval, backup |
| WRITE     | 12    | Validation and content transfer | Program deployment |
| REPLACE   | 18    | Includes collision detection | Program updates |

#### Essential Packet Formats

**Standard Acknowledgment:** `0000000205E000`

**Program Content Transfer:** `AAAAAAAA-04-BBBBBBBB-000D-CCCC-D`
- AAAAAAAA = 6 + content_length  
- BBBBBBBB = 2 + content_length  
- CCCC = content_length (TI encoding)

**Length Encoding (CCCC field):**
- ≤255 bytes: `[value] [00]`
- \>255 bytes: `[LSB] [MSB]`

#### Critical Implementation Points

1. **Character Encoding**: Use [complete reference table](#71-complete-character-encoding-reference)
2. **Length Fields**: Implement [TI's non-standard encoding](#24-tis-non-standard-length-encoding)  
3. **Acknowledgments**: Never skip ACK responses
4. **Collision Detection**: Always respect safety mechanisms in replace operations
5. **Field Calculations**: Verify DPS formulas for each operation type

---

*This documentation provides a comprehensive reference for the TI-BASIC program communication protocol on the TI-84 Plus CE calculator. All protocol details, encoding schemes, and communication flows have been thoroughly tested and verified through practical implementation. Future research will focus on discovering and documenting the deletion protocol.*