import flet as ft
import sqlite3


class ToDo:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.bgcolor = ft.colors.BLACK
        self.page.window.width = 350
        self.page.window.height = 450
        self.page.window.resizable = False
        self.page.window.always_on_top = True
        self.page.title = 'ToDo App'
        self.task = ''
        self.view = 'all'
        self.task_to_edit = None  # Variável para armazenar a tarefa sendo editada

        # Atualiza a tabela para garantir que ela tenha as colunas necessárias
        self.update_table_schema()

        self.results = self.db_execute('SELECT * FROM tasks ORDER BY day_num, start_time')
        self.main_page()

    def db_execute(self, query, params=[]):
        with sqlite3.connect('database.db') as con:
            cur = con.cursor()
            cur.execute(query, params)
            con.commit()
            return cur.fetchall()

    def update_table_schema(self):
        # Cria a tabela, se não existir, com as colunas corretas, incluindo o campo id
        self.db_execute(''' 
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID único para cada tarefa
                name TEXT,
                status TEXT,
                day TEXT,
                day_num INTEGER,
                start_time TEXT,
                end_time TEXT,
                difficulty TEXT,
                activity_type TEXT
            )
        ''')

    def checked(self, e, task_id):
        # Verifica se a checkbox foi marcada ou desmarcada
        is_checked = e.control.value
        # Atualiza o status da tarefa
        status = 'complete' if is_checked else 'incomplete'

        # Atualiza o status no banco de dados
        self.db_execute('UPDATE tasks SET status = ? WHERE id = ?', params=[status, task_id])

        if self.view == 'all':
            self.results = self.db_execute('SELECT * FROM tasks ORDER BY day_num, start_time')
        else:
            self.results = self.db_execute('SELECT * FROM tasks WHERE status = ? ORDER BY day_num, start_time', params=[self.view])

        self.update_task_list()

    def tasks_container(self):
        # Agrupa as tarefas por dia
        days_of_week = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
        
        # Organiza as tarefas por dia da semana
        tasks_by_day = {day: [] for day in days_of_week}

        for task in self.results:
            task_day = task[3]  # Dia da semana (agora o índice 3, pois o id é 0)
            tasks_by_day[task_day].append(task)

        controls = []

        # Para cada dia da semana, exibe as tarefas
        for day in days_of_week:
            day_tasks = tasks_by_day[day]
            if day_tasks:
                # Adiciona o título do dia
                controls.append(ft.Text(day, size=20, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD))

                # Adiciona as tarefas do dia ordenadas pelo horário de início
                day_tasks_sorted = sorted(day_tasks, key=lambda x: x[5])  # Ordena pelo start_time (índice 5)
                for task in day_tasks_sorted:
                    controls.append(
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Checkbox(
                                        label=task[1],  # Nome da tarefa
                                        on_change=lambda e, task_id=task[0]: self.checked(e, task_id),  # Passando o ID da tarefa
                                        value=True if task[2] == 'complete' else False
                                    ),
                                    ft.Text(task[3], width=100, text_align=ft.TextAlign.CENTER),  # Dia da semana
                                    ft.Text(task[5], width=70, text_align=ft.TextAlign.CENTER),   # Horário de Início
                                    ft.Text(task[6], width=70, text_align=ft.TextAlign.CENTER),   # Horário de Término
                                    ft.Text(task[7], width=70, text_align=ft.TextAlign.CENTER),   # Dificuldade
                                    ft.Text(task[8], width=100, text_align=ft.TextAlign.CENTER),   # Tipo Atividade
                                    
                                    # Botão de Editar
                                    ft.IconButton(
                                        icon=ft.icons.EDIT,
                                        on_click=lambda e, task=task: self.edit_task(e, task)  # Passando a tarefa inteira
                                    ),
                                    
                                    # Botão de Deletar
                                    ft.IconButton(
                                        icon=ft.icons.DELETE,
                                        on_click=lambda e, task_id=task[0]: self.delete_task(e, task_id)  # Passando o ID da tarefa
                                    )
                                ]
                            ),
                            padding=10,
                            margin=ft.Margin(left=0, top=0, right=0, bottom=5),
                            bgcolor=ft.colors.WHITE10,
                            border_radius=10
                        )
                    )

        return ft.ListView(
            controls=controls,
            expand=True,
        )

    def set_value(self, e):
        self.task = e.control.value

    def add(self, e, input_task):
        name = self.task
        status = 'incomplete'

        if name:
            self.db_execute(query='INSERT INTO tasks (name, status) VALUES (?, ?)', params=[name, status])
            input_task.value = ''
            self.results = self.db_execute('SELECT * FROM tasks ORDER BY day_num, start_time')
            self.update_task_list()

    def update_task_list(self):
        self.page.controls[-1] = self.tasks_container()  # Atualiza o último controle (tasks container)
        self.page.update()

    def main_changed(self, e):
        if e.control.selected_index == 0:
            self.results = self.db_execute('SELECT * FROM tasks ORDER BY day_num, start_time')
            self.view = 'all'
        elif e.control.selected_index == 1:
            self.results = self.db_execute('SELECT * FROM tasks WHERE status = "incomplete" ORDER BY day_num, start_time')
            self.view = 'incomplete'
        elif e.control.selected_index == 2:
            self.results = self.db_execute('SELECT * FROM tasks WHERE status = "complete" ORDER BY day_num, start_time')
            self.view = 'complete'

        self.update_task_list()

    def main_page(self):
        title = ft.Text("Minhas Tarefas", size=24, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)
        input_task = ft.TextField(
            hint_text="Clique no botão para adicionar uma tarefa",
            expand=True,
            on_change=self.set_value,
            text_size=int(self.page.window.width * 0.05)  
        )

        add_button = ft.FloatingActionButton(
            icon=ft.icons.ADD,
            on_click=self.show_add_form,  
        )

        input_bar = ft.Row(controls=[input_task, add_button])

        tabs = ft.Tabs(
            selected_index=0,
            on_change=self.main_changed,
            tabs=[ 
                ft.Tab(text="Todos"),
                ft.Tab(text="Em andamento"),
                ft.Tab(text="Finalizados")
            ],
        )

        tasks = self.tasks_container()

        self.page.add(title, input_bar, tabs, tasks)

    def delete_task(self, e, task_id):
        self.db_execute('DELETE FROM tasks WHERE id = ?', params=[task_id])

        if self.view == 'all':
            self.results = self.db_execute('SELECT * FROM tasks ORDER BY day_num, start_time')
        else:
            self.results = self.db_execute('SELECT * FROM tasks WHERE status = ? ORDER BY day_num, start_time', params=[self.view])

        self.update_task_list()

    def show_add_form(self, e):
        self.add_form_dialog = ft.AlertDialog(
            title=ft.Text("Adicionar Tarefa"),
            content=ft.Column(
                controls=[
                    ft.TextField(label="Título da Tarefa", expand=True),
                    ft.Dropdown(
                        label="Selecione o Dia da Semana",
                        options=[ft.dropdown.Option(day) for day in ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]],
                        expand=True
                    ),
                    ft.TextField(label="Horário de Início", expand=True),
                    ft.TextField(label="Horário de Término", expand=True),
                    ft.Dropdown(
                        label="Selecione a Dificuldade",
                        options=[ft.dropdown.Option(d) for d in ["Fácil", "Médio", "Difícil"]],
                        expand=True
                    ),
                    ft.Dropdown(
                        label="Tipo de Atividade",
                        options=[ft.dropdown.Option(t) for t in ["Estudo", "Trabalho", "Lazer"]],
                        expand=True
                    ),
                ]
            ),
            actions=[ 
                ft.TextButton("Cancelar", on_click=self.cancel_add_form),
                ft.TextButton("Confirmar", on_click=self.add_task_from_form)
            ]
        )
        self.page.dialog = self.add_form_dialog
        self.page.dialog.open = True
        self.page.update()

    def cancel_add_form(self, e):
        self.page.dialog.open = False
        self.page.update()

    def add_task_from_form(self, e):
        task_title = self.add_form_dialog.content.controls[0].value
        day = self.add_form_dialog.content.controls[1].value
        start_time = self.add_form_dialog.content.controls[2].value
        end_time = self.add_form_dialog.content.controls[3].value
        difficulty = self.add_form_dialog.content.controls[4].value
        activity_type = self.add_form_dialog.content.controls[5].value

        day_num = {
            'Segunda-feira': 1,
            'Terça-feira': 2,
            'Quarta-feira': 3,
            'Quinta-feira': 4,
            'Sexta-feira': 5,
            'Sábado': 6,
            'Domingo': 7
        }.get(day, 1)

        # Inserir nova tarefa no banco de dados
        self.db_execute('INSERT INTO tasks (name, status, day, day_num, start_time, end_time, difficulty, activity_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', 
                        params=[task_title, 'incomplete', day, day_num, start_time, end_time, difficulty, activity_type])

        self.results = self.db_execute('SELECT * FROM tasks ORDER BY day_num, start_time')
        self.update_task_list()

        self.page.dialog.open = False
        self.page.update()

    def edit_task(self, e, task):
        self.task_to_edit = task  # Armazena a tarefa a ser editada, incluindo o ID
        self.edit_form_dialog = ft.AlertDialog(
            title=ft.Text("Editar Tarefa"),
            content=ft.Column(
                controls=[
                    ft.TextField(value=task[1], label="Título da Tarefa", expand=True),  # Preenche com os dados atuais
                    ft.Dropdown(
                        value=task[3],
                        label="Selecione o Dia da Semana",
                        options=[ft.dropdown.Option(day) for day in ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]],
                        expand=True
                    ),
                    ft.TextField(value=task[5], label="Horário de Início", expand=True),
                    ft.TextField(value=task[6], label="Horário de Término", expand=True),
                    ft.Dropdown(
                        value=task[7],
                        label="Selecione a Dificuldade",
                        options=[ft.dropdown.Option(d) for d in ["Fácil", "Médio", "Difícil"]],
                        expand=True
                    ),
                    ft.Dropdown(
                        value=task[8],
                        label="Tipo de Atividade",
                        options=[ft.dropdown.Option(t) for t in ["Estudo", "Trabalho", "Lazer"]],
                        expand=True
                    ),
                ]
            ),
            actions=[ 
                ft.TextButton("Cancelar", on_click=self.cancel_edit_form),
                ft.TextButton("Confirmar", on_click=self.update_task_from_form)
            ]
        )
        self.page.dialog = self.edit_form_dialog
        self.page.dialog.open = True
        self.page.update()

    def cancel_edit_form(self, e):
        self.page.dialog.open = False
        self.page.update()

    def update_task_from_form(self, e):
        new_title = self.edit_form_dialog.content.controls[0].value
        new_day = self.edit_form_dialog.content.controls[1].value
        new_start_time = self.edit_form_dialog.content.controls[2].value
        new_end_time = self.edit_form_dialog.content.controls[3].value
        new_difficulty = self.edit_form_dialog.content.controls[4].value
        new_activity_type = self.edit_form_dialog.content.controls[5].value

        new_day_num = {
            'Segunda-feira': 1,
            'Terça-feira': 2,
            'Quarta-feira': 3,
            'Quinta-feira': 4,
            'Sexta-feira': 5,
            'Sábado': 6,
            'Domingo': 7
        }.get(new_day, 1)

        # Atualiza no banco de dados com o ID
        self.db_execute('''UPDATE tasks SET name = ?, day = ?, day_num = ?, start_time = ?, end_time = ?, difficulty = ?, activity_type = ? WHERE id = ?''',
                        params=[new_title, new_day, new_day_num, new_start_time, new_end_time, new_difficulty, new_activity_type, self.task_to_edit[0]])

        self.results = self.db_execute('SELECT * FROM tasks ORDER BY day_num, start_time')
        self.update_task_list()

        self.page.dialog.open = False
        self.page.update()

def main(page):
    ToDo(page)

ft.app(target=main)
