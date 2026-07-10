# Lesson Learned: D-LOTO Auto-Update Relaunch (2026-07-10)

## สรุปสั้นๆ

ฟีเจอร์ "อัพเดทเวอร์ชัน" (กดปุ่มแล้วโปรแกรมอัพเดทตัวเองและเปิดเวอร์ชันใหม่อัตโนมัติ) ใช้เวลาแก้บั๊ก
ยาวนานกว่าที่คาด เพราะมีบั๊กจริง **2 ตัวที่แยกกันโดยสิ้นเชิง** ซ้อนกันอยู่ในกระบวนการเดียว:

1. **Bug A** — frozen exe (PyInstaller onefile) ตัวหนึ่ง เปิด exe แบบ frozen อีกตัวไม่ได้ ("Failed to
   load Python DLL")
2. **Bug B** — เมื่อ Bug A ถูกแก้แล้ว โผล่บั๊กใหม่: exe เก่าไม่ยอมปิดตัวเองหลังอัพเดทสำเร็จ เพราะพยายาม
   ลบไฟล์ image ของตัวเองที่ Windows ล็อกไว้

Bug A ใช้ความพยายาม ~8 commits กว่าจะเจอ root cause ที่แท้จริง Bug B เจอและแก้ภายใน 1 commit
เพราะใช้ diagnostic evidence ที่เก็บมาระหว่างทาง

## Timeline / อาการที่เจอ

| ลำดับ | อาการ | สมมติฐานที่ลอง | ผล |
|---|---|---|---|
| 1 | `sys.exit()` ใน Tk callback ไม่ทำงาน | Tkinter กลืน exception | ✅ แก้ได้ (ไม่เกี่ยวกับ Bug A/B) |
| 2 | copy ไฟล์ล้มเหลวเงียบๆ | forward-slash path ใน `exe_path` จาก DB | ✅ แก้ได้ (เฉพาะ batch-script mechanism ที่ภายหลังถูกรื้อทิ้ง) |
| 3-6 | "Failed to load Python DLL" ตอนเปิด exe ใหม่ | ลอง delay, visible console, staging rename บน batch-script mechanism 4 รอบ | ❌ ไม่แก้ปัญหาเลยสักรอบ — **สัญญาณของ "3+ fixes failed → question architecture"** |
| 7 | (เหมือนเดิม) | user เสนอเทส `os.rename`/`Popen` แบบ pure Python ไม่ผ่าน cmd.exe เลย | ✅ ทำงานได้ทุกครั้ง → พิสูจน์ว่าปัญหาอยู่ที่ chain ของ `cmd.exe`/batch/`start` ไม่ใช่ที่ไฟล์หรือ copy logic |
| 8 | รื้อ batch script ทิ้งทั้งหมด, เขียนใหม่เป็น pure Python (`e56b7d0`) | Windows อนุญาตให้ rename exe ที่กำลังรันอยู่ได้ (พิสูจน์ด้วยเทสจริง) | ✅ ปัญหาเดิมหายไปจริง |
| 9 | orphan window ตอน rollback | onefile build จริงๆ เป็น 2 process (bootloader + interpreter); `Popen.kill()` ฆ่าแค่ตัวนอก | ✅ ใช้ `taskkill /T` ฆ่าทั้ง process tree |
| 10 | "Failed to load Python DLL" **กลับมาอีกครั้ง** หลังรื้อ batch script แล้ว | frozen exe ส่งต่อ env vars ของตัวเอง (`_MEIPASS2` ฯลฯ) ให้ child ที่เป็น frozen exe อีกตัว ทำให้ child extract ตัวเองพัง | ❌ Strip เฉพาะ prefix `_MEI*`/`_PYI*` ไม่พอ — error เดิมเป๊ะ, reproduce 100% |
| 11 | (เหมือนเดิม) | **เปลี่ยนวิธี**: หยุดเดา env var ตัวต่อไป → เพิ่ม diagnostic logging dump env จริงก่อน `Popen`, เทียบกับ baseline ของ python.exe ธรรมดา | ✅ **หลังจากใส่ diagnostic logging (โดยที่ยังไม่ได้แก้อะไรเพิ่ม) exe ใหม่กลับเปิดสำเร็จ** — สรุปว่า env-var stripping จาก commit ก่อนหน้า (`6863819`) จริงๆ ใช้ได้ผลอยู่แล้ว มีแค่บั๊กอื่นที่ยังบดบังผลลัพธ์อยู่ |
| 12 | exe ใหม่เปิดสำเร็จ แต่ exe เก่าไม่ปิด, ไม่มี popup สำเร็จ | ทดลองจริงบน Windows: rename exe ที่กำลังรันได้ แต่ **ลบไฟล์ที่ล็อกไว้ไม่ได้** (`PermissionError: WinError 5`) — โค้ด success path เรียก `os.remove(backup_exe)` ซึ่งคือ exe เก่าที่ยัง rename ตัวเองอยู่และกำลังรัน | ✅ เขียนเทสต์จำลองสถานการณ์นี้จริง (spawn exe แล้ว rename ระหว่างมันรันอยู่) → เทสต์ fail ตรงตามที่คาด → แก้โดยไม่ลบ `.bak` ทันที ปล่อยให้ startup ครั้งถัดไปลบแทน (`cleanup_stale_backup()`) |

## Root Cause ที่แท้จริงของแต่ละบั๊ก

### Bug A: "Failed to load Python DLL" ตอน frozen exe เปิด frozen exe อีกตัว

PyInstaller onefile build ที่รันอยู่จริงๆ เป็น **2 OS process** (bootloader ที่ extract ไฟล์ไปไว้ที่ temp
folder ชั่วคราว + ตัว interpreter จริงที่รันโค้ด) และมันสื่อสารกันผ่าน env vars ภายใน (เช่น
`_MEIPASS2`) เมื่อ process ที่กำลังรัน (ตัว interpreter) เรียก `subprocess.Popen()` เปิด exe ใหม่ (อีก
onefile build หนึ่ง) โดยไม่ตั้ง `env=` เอง มันจะ **ส่งต่อ environment ของตัวเองทั้งหมด** ให้ child
รวมถึง env vars ที่เป็น "ที่อยู่ของ bootloader ตัวเอง" ทำให้ child พยายาม extract ตัวเองโดยอ้างอิง state
ที่ผิด (ของ parent ไม่ใช่ของตัวเอง) แล้วพังตอนโหลด Python DLL

**หลักฐานที่ยืนยัน root cause**: เปิด exe ใหม่ผ่าน double-click (parent = explorer.exe, env สะอาด) หรือ
ผ่าน python.exe ธรรมดาที่ไม่ frozen (ไม่มี `_MEI*` vars เลย) ทำงานได้ทุกครั้ง แต่เปิดผ่าน frozen exe ที่
กำลังรันอยู่ พังทุกครั้ง — ตัวแปรร่วมเดียวที่ต่างกันคือ environment ที่ inherit มา

**Fix ที่ได้ผลจริง**: strip env vars ที่ขึ้นต้นด้วย `_MEI`/`_PYI` ออกก่อนส่งให้ child (`6863819`)

**บทเรียนสำคัญ**: fix นี้ *ใช้ได้ผลจริง* ตั้งแต่รอบแรก แต่เราคิดว่ามันยังไม่ได้ผลอยู่นานเกินจำเป็น เพราะ
บั๊ก B (ซึ่งเกิดขึ้น *หลังจาก* exe ใหม่เปิดสำเร็จแล้ว) ทำให้เห็นอาการที่คลุมเครือ (มีหน้าต่างซ้อนกัน,
ไม่มี popup) ซึ่งดูคล้ายกับว่า "อัพเดทยังไม่สำเร็จ" ทั้งที่จริงๆ มันสำเร็จไปแล้วในระดับ process

### Bug B: exe เก่าไม่ปิดตัวเองหลังอัพเดทสำเร็จ

เมื่ออัพเดทสำเร็จ, backup file (`.bak`) **คือไฟล์ image ของ exe เก่าที่กำลังรันอยู่นั่นเอง** (แค่ถูก
`os.rename()` เปลี่ยนชื่อ) Windows อนุญาตให้ **rename** ไฟล์ของ process ที่กำลังรันอยู่ได้ แต่ **ไม่
อนุญาตให้ลบ (delete)** ไฟล์นั้นจนกว่า process จะ exit จริง

โค้ดเดิมเรียก `os.remove(backup_exe)` ทันทีหลังจากพบว่า exe ใหม่เริ่มทำงานสำเร็จ (ยังอยู่ใน process
เก่าที่กำลังรัน) จึงโดน `PermissionError: [WinError 5] Access is denied` เสมอ — และเพราะ code
บรรทัดนี้อยู่ใน Tkinter button callback, exception ถูก Tkinter กลืนไปเงียบๆ ผลคือ:
- ไม่มี popup "อัพเดทสำเร็จ" โผล่ขึ้นมา
- `root.destroy()` และ `os._exit(0)` ที่ควรทำงานหลังจากนั้น **ไม่เคยถูกเรียก**
- exe เก่ายังรันค้างอยู่ พร้อมหน้าต่างเดิม กลายเป็นดูเหมือนมี 2 หน้าต่างซ้อนกัน

**หลักฐานที่ยืนยัน root cause**: เขียนสคริปต์ทดลองแยกต่างหาก จำลองการ spawn exe แล้ว rename ไฟล์
image ของมันระหว่างที่มันรันอยู่ — ยืนยันว่า rename ผ่านได้ แต่ delete ตามมาทันทีล้มเหลวด้วย error
เดียวกันเป๊ะ

**Fix**: ไม่ลบ `.bak` ในจังหวะนั้น (ปล่อยไว้เฉยๆ), เพิ่มฟังก์ชัน `cleanup_stale_backup()` ที่ลบ `.bak`
เก่าตอนแอปเปิดตัวครั้งถัดไป (ตอนนั้น process เก่าตายไปแล้วแน่นอน ไฟล์ไม่ถูกล็อกอีกต่อไป)

## บทเรียนสำหรับงานต่อไป (Lessons Learned)

1. **"3+ fixes ล้มเหลวติดกัน = สัญญาณเตือนสถาปัตยกรรม ไม่ใช่แค่โชคไม่ดี"** — การลอง fix บน batch-script
   mechanism 4 รอบติดโดยไม่ได้ผลเลย ควรเป็นสัญญาณให้หยุดและตั้งคำถามกับ mechanism ทั้งหมด (cmd.exe/batch/
   start) ตั้งแต่รอบที่ 3 ไม่ใช่รอบที่ 5

2. **อาการที่ "ดูเหมือนบั๊กเดิม" อาจไม่ใช่บั๊กเดิม** — หลังแก้ Bug A แล้ว อาการที่เห็น (มีหน้าต่างซ้อน,
   ไม่มี popup) ถูกตีความว่า "อัพเดทยังไม่สำเร็จเหมือนเดิม" ทั้งที่จริงๆ เป็นบั๊กคนละตัวที่เกิดขึ้น *หลัง*
   จุดที่ Bug A เคยพังไปแล้ว การเก็บ diagnostic evidence (dump env จริงๆ ก่อน `Popen`) คือสิ่งที่ทำให้
   แยกสองบั๊กออกจากกันได้ในที่สุด แทนที่จะเดาต่อไปเรื่อยๆ ว่า "fix ก่อนหน้ายังไม่พอ"

3. **เขียน diagnostic instrumentation ก่อนจะเดา fix รอบถัดไป** — แทนที่จะลองแก้ env var ตัวใหม่แบบสุ่ม
   (fix รอบที่ 6-7 ของปัญหาเดียวกัน) การเพิ่ม logging ที่ dump ข้อมูลจริง ณ จุดที่พัง แล้วเทียบกับ
   baseline ที่รู้ว่าทำงานได้ ทำให้เจอว่า fix เดิม (`6863819`) จริงๆ ใช้ได้ผลอยู่แล้ว และเปิดทางให้เจอ
   บั๊กที่สองซึ่งซ่อนอยู่ข้างหลัง

4. **PyInstaller onefile + relaunch ตัวเอง มีข้อควรระวัง 2 อย่างที่ไม่ชัดเจนจากเอกสารทั่วไป**:
   - Onefile build คือ 2 process เสมอ (bootloader + interpreter) — การ kill/manage process ต้องใช้
     `taskkill /T` (process tree) ไม่ใช่ `Popen.kill()` เดี่ยวๆ
   - Windows แยก "rename ไฟล์ที่กำลังรัน" (อนุญาต) ออกจาก "ลบไฟล์ที่กำลังรัน" (ไม่อนุญาตจนกว่า process
     จะตาย) — ดังนั้น mechanism ที่ rename exe ตัวเองแล้วหวังจะลบ backup ทันทีในกระบวนการเดียวกัน จะพัง
     เสมอ ต้องเลื่อนการลบไปเป็น "ครั้งถัดไปที่เปิดแอป" แทน

## Commit ที่เกี่ยวข้อง (ใหม่ → เก่า)

```
fe72c79 Fix old app not exiting after successful update: can't delete own running .bak   ← Bug B
6863819 Strip PyInstaller bootstrap env vars before launching the new exe                 ← Bug A (fix จริง)
df4bc89 Fix duplicate window on rollback (kill wrong PID), extend timeout, add success popup
e56b7d0 Replace batch-script relaunch with pure Python (os.rename works on a running exe)  ← จุดเปลี่ยนสถาปัตยกรรม
b7bbffd Copy new exe to a staging name and rename into place instead of copying directly
8713423 Fix intermittent DLL load failure: delay os._exit() after spawning the update script
6a60cc6 Make the update relaunch script visible with Thai status text
511cf23 Add 1s delay between copying the new exe and launching it
21721ab Fix copy failure on forward-slash exe_path values from the DB
a877b4a Fix crash after clicking dialog buttons: sys.exit() inside a Tk callback is swallowed
5a36ea4 Implement real auto-copy/relaunch logic for the update-version button
```

## สถานะปัจจุบัน (2026-07-10)

ทดสอบ end-to-end ผ่านแล้ว: กด "อัพเดทเวอร์ชัน" จาก 1.0.3 → เหลือหน้าต่าง 1.0.4 เพียงหน้าต่างเดียว
(ไม่มี 1.0.3 ค้าง) ยังเหลือยืนยันเพิ่มเติม (ไม่บล็อกการใช้งาน แต่ควรเช็ค):
- popup "อัพเดทสำเร็จ" ขึ้นจริงหรือไม่
- `C:\dtest\D-Loto.exe.bak` ถูกลบอัตโนมัติเมื่อเปิดแอปครั้งถัดไปหรือไม่
- เทส rollback (`exe_path` ผิด → ย้อนกลับอัตโนมัติ, exe เดิมยังใช้งานได้) ยังไม่ได้ re-test หลัง fix ล่าสุด
