from flask import Flask, render_template, url_for, request, flash, redirect, session
from database import conectar 

apps = Flask(__name__)
apps.secret_key = "12345"

# LOGIN

@apps.route('/')
def login():
    return render_template("login.html")


@apps.route('/', methods=["POST"])
def login_form():

    user = request.form['txtusuario']
    password = request.form['txtcontrasena']

    con = conectar()
    cursor = con.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE usuario=%s AND PASSWORD=%s", (user, password))
    user = cursor.fetchone()

    if user:
        session['usuario'] = user[4]  # suponiendo que aquí está el documento
        session['rol'] = user[3]

        if session['rol'] == 'empleado':
            return redirect(url_for("panelempleado"))
        elif session['rol'] == 'administrador':
            return redirect(url_for("inicio"))
    else:
        return redirect(url_for("login"))

@apps.route('/panelempleado')
def panelempleado():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    con = conectar()
    cursor = con.cursor(dictionary=True)
#de la tabla empleados se trae el nombre el apellido y el cargo, salario, horas extras, bonificacion, salud, pension, salario neto y el nombre del area a la que pertenece el empleado con una consulta sql usando el inner join para relacionar el documento del empleado con el documento del usuario y el id_area del empleado con el id_area del departamento, filtrando por el documento del usuario que ha iniciado sesión
    cursor.execute("""
        SELECT e.documento, e.nombre, e.apellido, e.cargo, e.salario, e.horas_extras, e.bonificacion, e.salud, e.pension, e.salario_neto, d.nombre_area
        FROM empleados e
        INNER JOIN departamentos d ON e.id_area = d.id_area
        WHERE e.documento = %s
    """, (session['usuario'],))
    datos_empleados = cursor.fetchone()

    cursor.close()
    con.close()
    print("SESSION:", session['usuario'])
    print("DATOS:", datos_empleados)

    return render_template("panelempleado.html", empleados=datos_empleados)
#                       actualizar_empleado
    
@apps.route('/actualizar_empleado', methods=['POST'])
def actualizar_emp():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    nombre = request.form['nombre']
    apellido = request.form['apellido']
    cargo = request.form['cargo']
    id_area = request.form['id_area']

    # VALIDACIONES
    if not nombre or not apellido or not cargo:
        flash("Todos los campos son obligatorios", "danger")
        return redirect(url_for('editar_empleado'))

    con = conectar()
    cursor = con.cursor()

    cursor.execute("""
        UPDATE empleados
        SET nombre=%s, apellido=%s, cargo=%s, id_area=%s
        WHERE documento=%s
    """, (nombre, apellido, cargo, id_area, session['usuario']))

    con.commit()
    cursor.close()
    con.close()

    flash("Datos actualizados correctamente", "success")
    return redirect(url_for('panelempleado'))


#editar empleado
@apps.route('/editar_empleado')
def editar_emp():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    con = conectar()
    cursor = con.cursor(dictionary=True)

    cursor.execute("""
        SELECT e.*, d.nombre_area 
        FROM empleados e
        INNER JOIN departamentos d ON e.id_area = d.id_area
        WHERE e.documento = %s
    """, (session['usuario'],))

    empleado = cursor.fetchone()

    cursor.execute("SELECT * FROM departamentos")
    departamentos = cursor.fetchall()

    cursor.close()
    con.close()

    return render_template("editar_emp.html", empleado=empleado, departamentos=departamentos)
# INICIO

@apps.route('/inicio')
def inicio():

    if 'usuario' not in session:
        return redirect(url_for('login'))

    con = conectar()
    cursor = con.cursor()

    cursor.execute("SELECT * FROM usuarios")
    lista_usuarios = cursor.fetchall()

    cursor.execute("""
        SELECT e.*, d.nombre_area FROM empleados e INNER JOIN departamentos d ON e.id_area = d.id_area""")
    lista_empleados = cursor.fetchall()

    cursor.execute("SELECT * FROM departamentos")
    lista_areas = cursor.fetchall()

    cursor.close()
    con.close()

    return render_template(
        "index.html",
        user=lista_usuarios,
        empleados=lista_empleados,
        areas=lista_areas
    )

# REGISTRAR USUARIO

@apps.route('/registrar', methods=["POST"])
def registrar():

    if 'usuario' not in session:
        return redirect(url_for('login'))

    usuario = request.form['usuario']
    password = request.form['password']
    rol = request.form['rol']
    documento = request.form['documento']

    con = conectar()
    cursor = con.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE usuario=%s", (usuario,))
    if cursor.fetchone():
        flash("Ese usuario ya existe", "warning")
        return redirect(url_for('inicio'))

    cursor.execute("SELECT * FROM usuarios WHERE documento=%s", (documento,))
    if cursor.fetchone():
        flash("Ese documento ya está registrado", "warning")
        return redirect(url_for('inicio'))

    cursor.execute(
        "INSERT INTO usuarios (usuario, PASSWORD, rol, documento) VALUES (%s, %s, %s, %s)",
        (usuario, password, rol, documento)
    )

    con.commit()
    cursor.close()
    con.close()

    flash("Usuario registrado correctamente", "success")
    return redirect(url_for('inicio'))

# REGISTRAR EMPLEADO

@apps.route('/registrar_empleado', methods=["POST"])
def registrar_empleado():

    if 'usuario' not in session:
        return redirect(url_for('login'))

    documento = request.form['documento']
    nombre = request.form['nombre']
    apellido = request.form['apellido']
    cargo = request.form['cargo']
    salario = float(request.form['salario'])

    horas = int(request.form['horas_extras'] or 0)
    bonificacion = float(request.form['bonificacion'] or 0)
    area = request.form['id_area']

    # CALCULOS
    valor_hora = salario / 240
    total_horas_extras = horas * valor_hora * 1.5

    salud = salario * 0.04
    pension = salario * 0.04

    salario_neto = salario + bonificacion + total_horas_extras - salud - pension

    con = conectar()
    cursor = con.cursor()

    cursor.execute("SELECT * FROM empleados WHERE documento=%s", (documento,))
    if cursor.fetchone():
        flash("Este empleado ya existe", "warning")
        return redirect(url_for('inicio'))

    cursor.execute("""
        INSERT INTO empleados 
        (documento, nombre, apellido, cargo, salario, horas_extras, bonificacion, salud, pension, salario_neto, id_area)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (documento, nombre, apellido, cargo, salario, horas, bonificacion, salud, pension, salario_neto, area))

    con.commit()
    cursor.close()
    con.close()

    flash("Empleado registrado correctamente", "success")
    return redirect(url_for('inicio'))

# ELIMINAR

@apps.route('/eliminar/<int:id>')
def eliminarusu(id):

    if 'usuario' not in session:
        return redirect(url_for('login'))

    con = conectar()
    cursor = con.cursor()

    cursor.execute("DELETE FROM usuarios WHERE id_usuario=%s", (id,))
    con.commit()

    cursor.close()
    con.close()

    flash("Usuario eliminado", "success")
    return redirect(url_for("inicio"))

# ELIMINAR EMPLEADO

@apps.route('/eliminar_empleado/<int:id>')
def eliminar_empleado(id):

    if 'usuario' not in session:
        return redirect(url_for('login'))

    con = conectar()
    cursor = con.cursor()

    cursor.execute("DELETE FROM empleados WHERE id_empleado=%s", (id,))
    con.commit()

    cursor.close()
    con.close()

    flash("Empleado eliminado", "success")
    return redirect(url_for("inicio"))

# EDITAR USUARIO

@apps.route('/editar/<int:id>')
def editar(id):

    if 'usuario' not in session:
        return redirect(url_for('login'))

    con = conectar()
    cursor = con.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE id_usuario=%s", (id,))
    usuario = cursor.fetchone()

    cursor.close()
    con.close()

    return render_template("editar.html", usuario=usuario)

# EDITAR EMPLEADO

@apps.route('/editar_empleado/<int:id>')
def editar_empleado(id):

    if 'usuario' not in session:
        return redirect(url_for('login'))

    con = conectar()
    cursor = con.cursor()

    cursor.execute("SELECT * FROM empleados WHERE id_empleado=%s", (id,))
    empleado = cursor.fetchone()

    cursor.close()
    con.close()

    return render_template("editar_empleado.html", empleado=empleado)

# ACTUALIZAR USUARIO

@apps.route('/actualizar', methods=["POST"])
def actualizar():

    if 'usuario' not in session:
        return redirect(url_for('login'))

    id = request.form['id']
    usuario = request.form['usuario']
    password = request.form['password']
    rol = request.form['rol']
    documento = request.form['documento']

    con = conectar()
    cursor = con.cursor()

    cursor.execute("""
        UPDATE usuarios 
        SET usuario=%s, PASSWORD=%s, rol=%s, documento=%s
        WHERE id_usuario=%s
    """, (usuario, password, rol, documento, id))

    con.commit()
    cursor.close()
    con.close()

    flash("Usuario actualizado", "success")
    return redirect(url_for('inicio'))

# ACTUALIZAR EMPLEADO

@apps.route('/actualizar_empleado', methods=["POST"])
def actualizar_empleado():

    if 'usuario' not in session:
        return redirect(url_for('login'))

    id = request.form['id']
    documento = request.form['documento']
    nombre = request.form['nombre']
    apellido = request.form['apellido']
    cargo = request.form['cargo']
    salario = float(request.form['salario'])

    horas = int(request.form['horas_extras'] or 0)
    bonificacion = float(request.form['bonificacion'] or 0)
    area = request.form['id_area']

    # RECALCULAR
    valor_hora = salario / 240
    total_horas_extras = horas * valor_hora * 1.5

    salud = salario * 0.04
    pension = salario * 0.04

    salario_neto = salario + bonificacion + total_horas_extras - salud - pension

    con = conectar()
    cursor = con.cursor()

    cursor.execute("""
        UPDATE empleados 
        SET documento=%s, nombre=%s, apellido=%s, cargo=%s,
            salario=%s, horas_extras=%s, bonificacion=%s,
            salud=%s, pension=%s, salario_neto=%s, id_area=%s
        WHERE id_empleado=%s
    """, (
        documento, nombre, apellido, cargo,
        salario, horas, bonificacion,
        salud, pension, salario_neto, area, id
    ))

    con.commit()
    cursor.close()
    con.close()

    flash("Empleado actualizado correctamente", "success")
    return redirect(url_for('inicio'))

#   EMPLEADOS 


#  SALIR

@apps.route('/salir')
def salir():
    session.clear()
    return redirect(url_for('login'))

#  MAIN 

if __name__ == '__main__':
    apps.run(debug=True)