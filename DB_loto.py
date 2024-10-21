import sqlite3
import os
import datetime
from datetime import datetime

# DESCRIPTION: Select the Folder to create DB
directory =  "C:/Users/wechp/OneDrive - PTT GROUP/PTTLNG/3.Project/LNG Project/2024/2.LOTO Project"
db_name = "loto_data.db"
database_path = os.path.join(directory,db_name)

# DESCRIPTION: Create CONNECTION to the DB (sqlite3-)atabase
conn = sqlite3.connect(database_path)

# DESCRIPTION: Create CURSOR for do database operation
c = conn.cursor()

# DESCRIPTION: Create table loto_overview
c.execute(""" CREATE TABLE IF NOT EXISTS loto_overview (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    loto_no TEXT,
                    work_title TEXT,
                    owner TEXT,
                    lock_date TEXT,
                    status TEXT)""")

# DESCRIPTION: Insert data to loto_overview table
def insert_data(loto_no,work_title,owner,telephone):
    # CREATE
    with conn:
        command =  'INSERT INTO loto_overview VALUES (?,?,?,?,?,?)'
        c.execute(command,(None,loto_no,work_title,owner,telephone,'new'))
    conn.commit() # Save database

# def testins():
    ################################ DESCRIPTION: TEST INSERT DATA
    insert_data('1','Isolate Valve Tie-in to GSP#7','Project','45259')
    insert_data('21','Isolate for stopping leak of portable water supply to EWS','MT.Mech','45372')
    insert_data('45','Isolate manual valve chlorine dosing bay D','MT.Mech','45415')
    insert_data('18','Isolating for investigation Junction box In-tank pump 3B','MT.Mech','45461')
    insert_data('23','Isolate CWG for Glass house 2','Project','45500')
    insert_data('26','Drain HP Pump E for overhaul work','LO','45512')
    insert_data('29','Isolate LNG-1128 for overhaul HP Pump E','LO','45515')
    ################################ DESCRIPTION: TEST INSERT DATA

# DESCRIPTION: Feth data from loto_overview table to Show
def view_data():
    # READ
    with conn:
        command = 'SELECT * FROM loto_overview'
        c.execute(command)
        result = c.fetchall()
        # print(result)
    return result

def view_data_new():
    with conn:
        command = """SELECT new_loto_no, new_work_title, new_incharge_dept, new_owner, new_prepare, new_lock_date, status
        FROM loto_new
        WHERE status = 'Waiting' OR status = 'Rejected'
        """
        c.execute(command)
        result = c.fetchall()
    return result

# DESCRIPTION: Create DB loto_new
c.execute(""" CREATE TABLE IF NOT EXISTS loto_new (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_id TEXT,
                    new_work_title TEXT,
                    new_incharge_dept TEXT,
                    new_owner TEXT,
                    new_telephone TEXT,
                    new_area TEXT,
                    new_equipment TEXT,
                    new_lock_date TEXT,
                    new_loto_no TEXT,
                    new_loto_keys TEXT,
                    new_pid_pdf TEXT,
                    new_override_list TEXT,
                    new_remark TEXT,
                    new_prepare TEXT,
                    new_verify TEXT,
                    new_approve TEXT,
                    status TEXT)""")

# DESCRIPTION: Insert data to loto_new DB
def insert_new_loto(log_id,new_work_title,new_incharge_dept,new_owner,
                new_telephone,new_area,new_equipment,new_lock_date,
                new_loto_no,new_loto_keys,new_pid_pdf,new_override_list,new_remark,
                new_prepare,new_verify,new_approve):
    # CREATE
    with conn:
        command =  'INSERT INTO loto_new VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
        c.execute(command,(None,log_id,new_work_title,new_incharge_dept,new_owner,
                new_telephone,new_area,new_equipment,new_lock_date,
                new_loto_no,new_loto_keys,new_pid_pdf,new_override_list,new_remark,
                new_prepare,new_verify,new_approve,'Waiting'))
    conn.commit() # Save database

# DESCRIPTION: Feth data from loto_new to loto_overview for show
def transfer_data():
    with conn:
        # command0 = """DELETE FROM loto_overview"""
        # c.execute(command0)
        command = """
        INSERT INTO loto_overview (loto_no, work_title, owner, lock_date, status) 
        SELECT new_loto_no, new_work_title, new_incharge_dept, new_lock_date, status
        FROM loto_new 
        WHERE status IN ('Active', 'Onsite')
        AND (new_loto_no, new_work_title, new_incharge_dept, new_lock_date) NOT IN (
        SELECT loto_no, work_title, owner, lock_date FROM loto_overview)
        """
        c.execute(command)
        print("data transfered")
    conn.commit()

def add_data_to_popup(loto_no, work_title, lock_date):
    with conn:
        command = """
        SELECT * FROM loto_new
        WHERE new_loto_no = ? AND new_work_title = ? AND new_lock_date = ?
        """
        c.execute(command, (loto_no, work_title, lock_date))
        result = c.fetchall()  # Fetch all the matching records
        # print(f'Result from add_data_to_popup is: {result}')
    return result

def confirm_button_approve(GUI4, GUI3, v_loto_no, v_work_title, v_lock_date, v_remark, v_approve,state,refresh_callback=None):
    # print(f'v_loto_no: {v_loto_no}')
    # print(f'v_remark: {v_remark}')
    remark_value0 = v_remark.get()
    remark_value = date_str(3) + '\n' + remark_value0
    approve_value = v_approve.get()
    print('working on the confirm_button_approve')
    print(f'v_loto_no: {v_loto_no}')
    print(f'v_work_title: {v_work_title}')
    print(f'v_lock_date: {v_lock_date}')
    with conn:
        command_fetch = """
        SELECT new_remark, new_approve, status
        FROM loto_new
        WHERE new_loto_no = ? AND new_work_title = ? AND new_lock_date = ?
        """
        # print('working on the fetch')
        c.execute(command_fetch, (v_loto_no, v_work_title, v_lock_date))
        result = c.fetchone()
        # print(f'result: {result}')

        if result:
            # Extract the existing remark, approve, and status
            existing_remark = result[0]  # This is the existing remark
            existing_approve = result[1]  # This is the existing approval person
            current_status = result[2]  # This is the current status
            

            # Check if the status is "Waiting" before proceeding
            if current_status == "Waiting" or current_status == "Rejected":
                # 1. Add the new remark after the old one (on a new line)
                updated_remark = f"{existing_remark}\n{remark_value}" if existing_remark else remark_value
                # 2. Replace the old approval with the new one
                updated_approve = approve_value
                # 3. Change the status to "Active", Wating -> Active for test
                # print('Working on the state')
                if state == True:
                    updated_status = "Active"
                    # print(f'updated_status: {updated_status}')
                elif state == False:
                    updated_status = "Rejected"
                # 4. Update the lock date to the current date
                updated_lock_date = date_str(1)
                # print(f'updated_lock_date: {updated_lock_date}')

            # Update the record in the database
                command_update = """
                UPDATE loto_new
                SET new_remark = ?, new_approve = ?, status = ?, new_lock_date = ?
                WHERE new_loto_no = ? AND new_work_title = ? AND new_lock_date = ?
                """
                c.execute(command_update, (updated_remark, updated_approve, updated_status, updated_lock_date, v_loto_no, v_work_title, v_lock_date))
                conn.commit()   
    transfer_data()

    if refresh_callback:
        refresh_callback()

    print("GUI DESTROY")
    GUI4.destroy()
    GUI3.destroy()

def confirm_button_update(GUI4, GUI3,v_loto_no, v_work_title, v_lock_date, v_pdf_update, v_override_update, v_remark0,v_update0,state,refresh_callback=None):
    remark_value0 = v_remark0.get()
    v_update0 = v_update0.get()
    remark_value = date_str(3) + ' update by '+ v_update0 + '\n' + remark_value0
    pdf_value = v_pdf_update.get()
    override_value = v_override_update.get()
    
    print('working on the confirm_button_update')
    print(f'v_loto_no: {v_loto_no}')
    print(f'v_work_title: {v_work_title}')
    print(f'v_lock_date: {v_lock_date}')
    print(f'remark_value: {remark_value}')
    with conn:
        command_fetch = """
        SELECT new_pid_pdf, new_override_list, new_remark
        FROM loto_new
        WHERE new_loto_no = ? AND new_work_title = ? AND new_lock_date = ?
        """
        # print('working on the fetch')
        c.execute(command_fetch, (v_loto_no, v_work_title, v_lock_date))
        result = c.fetchone()
        print(f'result: {result}')

        if result:
            # Extract the data
            existing_pdf = result[0]  # This is the existing pdf url
            existing_override = result[1]  # This is the existing override url
            existing_remark = result[2]  # This is the existing existing_remark
  
            # 1. Add the new remark after the old one (on a new line)
            updated_remark = f"{existing_remark}\n{remark_value}" if existing_remark else remark_value
            # 2. Replace the old pdf with the new one
            if pdf_value:
                updated_pdf = pdf_value
            else:
                updated_pdf = existing_pdf
            # 3. Replace the old override with the new one
            if override_value:
                updated_override = override_value
            else:
                updated_override = existing_override

            print(f'updated_pdf: {updated_pdf}')
            print(f'updated_override: {updated_override}')

            # Update the record in the database
            command_update = """
            UPDATE loto_new
            SET new_pid_pdf = ?, new_override_list = ?, new_remark = ?
            WHERE new_loto_no = ? AND new_work_title = ? AND new_lock_date = ?
            """
            c.execute(command_update, (updated_pdf, updated_override, updated_remark, v_loto_no, v_work_title, v_lock_date))
            conn.commit()

def date_str(select):
    a = datetime.now()
    day_today = a.strftime("%d")
    month_today = a.strftime("%m")
    year_today = a.strftime("%y")
    date_today = day_today+'/'+month_today+'/'+year_today
    remark_date = date_today+' '+a.strftime("%H:%M")
    if select == 1:
        return date_today
    elif select == 3:
        return remark_date