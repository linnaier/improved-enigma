# 导入pymysql模块，用于Python连接操作MySQL数据库
import pymysql

# 数据库连接配置信息
db_config = {
    "host": "127.0.0.1",       # MySQL服务器地址，127.0.0.1代表本地数据库
    "port": 3306,               # MySQL默认端口号
    "user": "root",             # 数据库登录用户名
    "password": "jyf157622",    # 数据库登录密码
    "database": "bookmanagesystem_db", # 需要操作的数据库名称
    "charset": "utf8mb4"        # 字符集，支持中文、emoji表情
}

# 函数：获取数据库连接对象
def get_conn():
    # 根据配置信息建立连接并返回连接通道conn
    return pymysql.connect(**db_config)

# 工具函数：删除书籍之后，自动重置id，保证id连续没有空缺
def reset_id():
    conn = get_conn()
    # 创建游标cursor，游标是执行SQL、获取数据库数据的"遥控器"
    cursor = conn.cursor()
    # 重置自增计数器
    cursor.execute("ALTER TABLE bookinformation AUTO_INCREMENT = 1")
    # 定义临时变量num初始值为0
    cursor.execute("SET @num = 0")
    # 遍历所有图书，重新依次分配id：1,2,3,4...
    cursor.execute("UPDATE bookinformation SET id = (@num:=@num+1) ORDER BY id")
    # 提交事务，使修改生效
    conn.commit()
    # 关闭游标
    cursor.close()
    # 关闭数据库连接
    conn.close()

# 功能函数：查看全部书籍信息
def show_all():
    conn = get_conn()
    cursor = conn.cursor()
    # 查询所有图书，按照id从小到大排序
    cursor.execute("SELECT id,name,isbn,number FROM bookinformation ORDER BY id")
    # fetchall()：取出查询到的全部数据
    all_books = cursor.fetchall()
    print("\n=========全部图书列表=========")
    # 判断是否没有任何书籍
    if not all_books:
        print("暂无任何书籍数据")
    else:
        # 格式化表头，<代表左对齐
        print(f"{'编号':<4}{'书名':<18}{'ISBN':<12}{'库存数量':<6}")
        print("-" * 42)
        # 循环遍历每一条图书数据
        for book in all_books:
            bid, bname, bisbn, bnum = book
            print(f"{bid:<4}{bname:<18}{bisbn:<12}{bnum:<6}")
    cursor.close()
    conn.close()

# 功能函数：添加书籍，参数new_name为外部传入的书籍名称
def add(new_name):
    conn = get_conn()
    cursor = conn.cursor()
    # 接收用户输入ISBN，strip()去除首尾空格
    isbn = input("请输入书籍ISBN：").strip()
    num = input("请输入书籍数量：").strip()
    # 判断输入的数量是否为纯数字
    if not num.isdigit():
        print("数量必须为数字，添加失败")
        cursor.close()
        conn.close()
        return
    add_num = int(num)
    # 校验新增书籍ISBN不能重复
    cursor.execute("SELECT id FROM bookinformation WHERE isbn=%s", (isbn,))
    # fetchone() 获取第一条查询结果，不为空代表ISBN已存在
    if cursor.fetchone():
        print("ISBN号已存在，无法添加！")
        cursor.close()
        conn.close()
        return
    # 查询数据库里是否存在同名书籍
    cursor.execute("SELECT id,number FROM bookinformation WHERE name=%s", (new_name,))
    res = cursor.fetchone()
    if res:
        # 同名书籍：只累加库存，不再新增一行记录
        old_id, old_num = res
        new_total = old_num + add_num
        cursor.execute("UPDATE bookinformation SET number=%s WHERE id=%s", (new_total, old_id))
        conn.commit()
        print(f"书籍已存在，库存自动+{add_num}，当前总数量：{new_total}")
    else:
        # 不存在同名书籍，插入新书籍记录
        insert_sql = "INSERT INTO bookinformation(name,isbn,number) VALUES(%s,%s,%s)"
        cursor.execute(insert_sql, (new_name, isbn, add_num))
        conn.commit()
        print('添加完成')
    cursor.close()
    conn.close()

# 功能函数：删除书籍，del_name为待删除书籍名称
def delete(del_name):
    conn = get_conn()
    cursor = conn.cursor()
    # 查询该书籍是否存在
    cursor.execute("SELECT name FROM bookinformation WHERE name=%s", (del_name,))
    if not cursor.fetchone():
        print('未找到该书籍，无法删除')
        cursor.close()
        conn.close()
        return
    # 执行删除SQL语句
    del_sql = "DELETE FROM bookinformation WHERE name=%s"
    cursor.execute(del_sql, (del_name,))
    conn.commit()
    print('delete successfully')
    cursor.close()
    conn.close()
    # 删除完成后调用函数，重新整理id，消除断号
    reset_id()
    # 新建连接，查询并打印当前所有书籍名称
    conn2 = get_conn()
    cur2 = conn2.cursor()
    cur2.execute("SELECT name FROM bookinformation")
    res = cur2.fetchall()
    print('当前全部书籍：')
    for book in res:
        print(book[0])
    cur2.close()
    conn2.close()

# 功能函数：修改书籍信息，old_bookname为待修改书籍原名称
def update(old_bookname):
    conn = get_conn()
    cursor = conn.cursor()
    # 根据原书名查询书籍id和原始ISBN
    cursor.execute("SELECT id,isbn FROM bookinformation WHERE name=%s", (old_bookname,))
    res = cursor.fetchone()
    if not res:
        print("未找到该书籍，退出修改")
        cursor.close()
        conn.close()
        return
    book_id, old_isbn = res
    new_name=input("请输入修改后的新书名：").strip()
    # 判断书名是否为空
    if new_name=="":
        print("书名不能为空，退出修改")
        cursor.close()
        conn.close()
        return
    new_isbn = input("输入新ISBN(不修改直接回车)：").strip()
    new_num = input("输入新数量(不修改直接回车)：").strip()

    # ISBN唯一性校验
    if new_isbn != "":
        # 查询【除了本书自身】之外，是否有其他图书占用该ISBN
        cursor.execute("SELECT id FROM bookinformation WHERE isbn=%s AND id != %s", (new_isbn, book_id))
        if cursor.fetchone():
            print("ISBN号已存在，修改失败！")
            cursor.close()
            conn.close()
            return

    # 动态拼接更新语句
    update_sql = "UPDATE bookinformation SET name=%s"
    params = [new_name]
    # 用户输入了新ISBN，则拼接字段
    if new_isbn:
        update_sql += ",isbn=%s"
        params.append(new_isbn)
    # 用户输入合法数字数量，则拼接字段
    if new_num.isdigit():
        update_sql += ",number=%s"
        params.append(int(new_num))
    # 添加条件：只修改当前这本书
    update_sql += " WHERE id=%s"
    params.append(book_id)
    cursor.execute(update_sql, params)
    conn.commit()
    print('update successfully')
    # 查询并展示修改后所有书籍
    cursor.execute("SELECT name FROM bookinformation")
    res = cursor.fetchall()
    print("查看所有书籍:")
    for book in res:
        print(" "+book[0])
    cursor.close()
    conn.close()

# ----------------主程序入口，系统菜单循环----------------
while True:
    print("\n----------欢迎使用图书管理系统----------")
    print("按1查看所有书籍")
    print("按2增加书籍")
    print("按3删除书籍")
    print("按4修改书籍")
    print("按5查找书籍")
    print("按6退出系统")
    try:
        # 接收用户输入选项，尝试转为数字
        n=int(input("请输入"))
    except ValueError:
        # 用户输入文字、符号时报错捕获，防止程序崩溃
        print("输入无效，请输入正确的服务数字")
        continue
    # 根据输入数字选择对应功能
    if n==1:
        show_all()
    elif n == 2:
        name=input("请输入书籍名称：").strip()
        if name == "":
            print('书名不能为空，取消本次添加')
            continue
        add(name)
    elif n==3:
        book=input('请输入要删除的书籍：').strip()
        delete(book)
    elif n==4:
        bookname=input('请输入要修改的书籍名称：').strip()
        update(bookname)
    elif n==5:
        # 查找指定书籍
        find_bookname=input('请输入要查找的书籍：').strip()
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id,name,isbn,number FROM bookinformation WHERE name=%s", (find_bookname,))
        data = cursor.fetchone()
        if data:
            print("找到书籍")
            print(f"编号:{data[0]} 书名:{data[1]} ISBN:{data[2]} 数量:{data[3]}")
        else:
            print('不存在该书籍')
        cursor.close()
        conn.close()
    elif n==6:
        print('退出成功')
        break  # 跳出while无限循环，结束程序
    else:
        # 输入数字不在1~6范围内
        print("输入服务数字无效，请重新输入")