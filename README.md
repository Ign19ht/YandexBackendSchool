## Структура базы данных
Использовалась библитека sqlalchemy
Для хранения данных используется postgreSQL.

Все таблицы описаны в backend/models.py.

Все функции описаны в backend/crud.py

### Таблицы:
#### Таблица Items
Хранит данные (Папки, Файлы) после последного обновления
* id: primary key, type - String 
* url: type - String
* parentId: type - String
* size: type - Integer
* type: type - Enum(FOLDER, FILE)
* date: type - DateTime
#### Таблица History
Хранит историю обновленния данных с теми параметрами, которые были на момет времени date
* id: primary key, type - String 
* url: type - String
* parentId: type - String
* size: type - Integer
* type: type - Enum(FOLDER, FILE)
* date: primary key, type - DateTime

### Функции, работающие с таблицей
* add_item: Принимает текущую сессию БД, объект для добавления и время добавления. Добавляет item в таблицу items и hystory.
* delete_item: Принимает тукущую сессию БД и id объекта. Удаляет объект из таблицы items.
* get_item: Принимает тукущую сессию БД и id объекта. Возвращет объект с нужным id.
* search_children: Принимает текущую сессию БД и id объекта. Возвращает список объектов с параметром childId равному id входного объекта.
* get_updates: Принимает текущую сессию БД и дату. Возвращает список объектов из таблицы tables, которые были обновлены позднее входной даты.
* remove_from_history: Принимает текущую сессию БД и id объекта. Удаляет все записи из истории (таблица history) объекта с входным id.
* update_folder_size: Принимает текущую сессию БД, id папки, новый размер папки и дату обновления. Обновляет данные размера папки и записывает это в историю папки.
* get_history: Принимает текущую сессию БД, id объекта и имеет несколько вариаций
  * get_history: Принимает стартовую и конечную дату. Возращает историю по объекту в данном временом диапозоне.
  * get_history_from: Принимает стартовую дату. Возвращает историю по объекту начиная с входной даты.
  * get_history_to: Принимает конечную дату. Возвращает историю по объекту до входной даты.
  * get_all_history: Возвращает всю историю по объекту.

## API
Использовалась библиотека fastapi.

Функции описаны в backend/main.py.

Схемы API запросов описаны в backend/schemas с использование библиотеки pydantic.

### Функции
* imports: Описывает запрос "/imports". Проверяет запрос на валидность и добавляет объекты в БД через команду crud.add_items
* delete: Описывает запрос "/delete/{id}". Удаляет объект с входным id из БД через команду crud.delete_item
* get_node: Описывает запрос "/nodes/{id}". Возвращает данные по объекту с входным id. Использует команду crud.get_item
* get_updates: Описывает запрос "/updates". Возвращает данные по объектам, которые были обновлены позднее входной даты. Использует команду crud.get_updates
* get_history: Описывает запрос "/node/{id}/history". Возвращает историю по объекту в заданом временом диапозоне. В зависимости от входных данных использует команды: crud.get_history, .get_history_from, .get_history_to и .get_all_history
### Дополнительные функции
* check_validity: Проверяет входные данные на валидность.
* get_children: Рекурсивная функция, возвращающая данные о "детях" объекта.
* delete_children: Рукурсивная функция, удаляющая "детей" папки, если они существуют
* update_folder_size: Обновляет размер папки
### Запуск API
Для работы API сервера использовалась библиотека uvicorn.
Сервер работает по адресу "0.0.0.0:80"
## Сборка и запуск
Сборка и запуск осуществаляется в Docker

Проект разбит на два контейнера:
* Контейнер с сервером БД
* Контейнер с API сервером

Для сборки используется команда: docker-compose -f docker-compose.dev.yaml build
Для запуска: docker-compose -f docker-compose.dev.yaml up
## Используемые библиотеки и пакеты
Python библиотеки прописаны в requirements.txt:
* uvicorn
* fastapi
* psycopg2-binary
* sqlalchemy
* pydantic
Используемые пакеты для запуска: 
* docker
* docker-compose
---
Проверка работы проходила на операционой системе Manjaro