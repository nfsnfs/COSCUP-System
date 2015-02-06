COSCUP-System
=============

COSCUP 研討會的個資中心

Introduction
------------

這個系統是為了解決 COSCUP 籌辦時，在人事資料遭遇的以下幾個問題:
* 個資管理
* 資料一致性
* 自動化處理

我們使用幾個額外的函式庫與 framework: Mongokit、Flask、pyjwt。

在 MongoDB 我們使用 coscup2015 這個 db，並有三個 collection: user_data、user_account、permission。

一開始請先執行:
    python initial_setup.py

會先將 permission collection 做最基本的設定。

權限的設計在 permission_setting.py 可以看到，目前設計為將每個 role 的每個 field 都各自設定權限，
例如，以下表示行政組組員可以被哪些 role 讀取或寫入:

    team_admin_permission = { 
        'role': 'team-admin',
        'fields': { 'id': { 'read': [], 'write': ['self'] },
                    'team': { 'read': [], 'write': ['self'] },
                    'last_name': { 'read': ['self', 'admin'], 'write': ['self'] },
                    'first_name': { 'read': ['self', 'admin'], 'write': ['self'] },
                    'nickname': { 'read': [], 'write': ['self'] },
                    'gender': { 'read': ['self', 'admin', 'team-admin'], 'write': ['self'] },
                    'email': { 'read': ['self', 'admin', 'team-admin'], 'write': ['self'] },
                    'phone': { 'read': ['self', 'admin'], 'write': ['self'] },
                    't-shirt': { 'read': ['self', 'admin'], 'write': ['self'] },
                    'food': { 'read': ['self', 'admin'], 'write': ['self'] },
                    'certificate': { 'read': ['self', 'admin', 'team-admin'], 'write': ['self'] },
                    'accommodation': { 'read': ['self', 'admin', 'team-admin'], 'write': ['self'] },
                    'traffic': { 'read': ['self', 'admin', 'team-admin'], 'write': ['self'] },
                    'origin': { 'read': ['self', 'admin', 'team-admin'], 'write':['self'] },
                    'birthday': { 'read': ['self', 'admin'], 'write':['self'] },
                    'new': { 'read': ['self', 'admin', 'team-admin'], 'write':['self'] },
                    'language': { 'read': ['self', 'admin', 'team-admin'], 'write':['self'] },
                    'skill': { 'read': ['self', 'admin', 'team-admin'], 'write':['self'] },
                    'others': { 'read': ['self', 'admin', 'team-admin'], 'write':['self'] },
                    'redmine': { 'read': [], 'write':['self'] },
                    'project': { 'read': [], 'write':['self', 'admin'] },
                    'role': { 'read': [], 'write':['admin'] },
                    'comment': { 'read': ['admin'], 'write':['admin'] },
        }
    }

P.S. 其中 read 若為 []，表示所有工作人員都可讀；admin 是系統管理者。


Progress
--------

目前進度: 完成與工作人員系統相關的幾個 API

*   /login - Login 登入

    method: POST

    parameter: 
        { "user": user_id, "passwd": user_passwd }

    response:
        { "token": token }

*   /invite - 邀請 (admin only)
    
    method: POST

    header:
        Token: token

    parameter:
        [{ "nickname": nickname, "email": email, "team": team }]

    response:
        { "msg": "ok", "email: [ "email1", "email2", ... ]}

        
*   /apply/&lt;apply_token&gt;- Apply account 申請帳號 (改成邀請制)
    
    method: POST
    
    parameter:
        { "user": user_id, "passwd": user_passwd, "email": user_email }

    response:
        { "msg": "ok" }

*   /user - Access my information 存取自己相關資訊

    method: GET

    header:
        Token: token

    
    method: POST - create / PUT - update

    header:
        Token: token

    parameter:
        Example:
           { "team": ["team-admin"], "last_name": "陳", "first_name": "nfsnfs", 
             "nickname": "nfs", "gender": "male", "email": "nfsnfs@lala.tw", 
             "phone": "0911-111-111", "t-shirt": "XL", "food": "葷", "certificate": true,
             "accommodation": true, "traffic": false, "origin": "中壢", "birthday": 0, 
             "new": false, "language": ["English"], "skill": [], "others": "COSCUP 萬歲!",
             "project": [], "redmine": "nfsnfs" }

    可用欄位:
    * 'id': basestring,         使用者 ID (系統設定)
    * 'team': list,             組別      
    * 'team-lead': list,        組長      (系統另外設定)
    * 'last_name': unicode,     姓
    * 'first_name': unicode,    名
    * 'nickname': unicode,      綽號
    * 'gender': basestring,     性別
    * 'email': basestring,      E-mail
    * 'phone': basestring,      電話
    * 't-shirt': basestring,    T-shirt 大小
    * 'food': unicode,          食物偏好 
    * 'certificate': bool,      是否需要感謝狀
    * 'accommodation': bool,    住宿需求
    * 'traffic': bool,          交通需求 
    * 'origin': unicode,        出發地
    * 'birthday': int,          生日早於 1995/8/15 -> 0, 晚於 1995/8/16 -> 1
    * 'new': bool,              新血
    * 'language': list,         語言專長 
    * 'skill': list,            其他專長
    * 'others': unicode,        備註
    * 'project': list,          參與 project
    * 'role': list,             角色權限    (系統設定)
    * 'redmine': basestring,    redmine 帳號
    * 'comment': unicode,       Admin 用的備註欄位

ToDo
----

1.  自動開啟 Redmine 帳號，並設定權限
2.  發送 Slack 邀請函
3.  將新 user email 放入 coscup-staff mailing list
4.  放入各組通訊錄
5.  寄送歡迎信
6.  /search API: 可以搜尋特定欄位，也可以搜尋哪些人沒有 or 沒填某些欄位
7.  /project API: 讓組長可以開啟 project，其他人可自由加入 
8.  整理 code
