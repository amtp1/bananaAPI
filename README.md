# bananaAPI

## Основные функции

> Получение текущего баланса
----
> Получение ордеров по символу, по желанию сохранить в excel файл
----
> Прогон волатильности

## Введение
----
Для начала нам нужно добавить `конфигурационные данные` для корректной работы скрипта. Получить их можно из личного аккаунта [Binance API](https://www.binance.com/ru/my/settings/api-management). Нам понадобятся два значения API KEY и SECRET KEY. После получения, в папке `config` создаем файл с названием и расширением `config.yaml`.
После создания вписываем значения в файл.

----

### Содержимое файла `config.yaml`:
```
API_KEY: ваш API KEY
SECRET_KEY: ваш SECRET KEY
```
После внесения данных, сохраняем файл и приступаем к дальнейшим действиям.

## Запуск
----

#### Перед запуском желательно, чтобы на ПК были установлены `Python >= 3.7` версии и `пакетный менеджер (PIP)`.
----

### Сначала создадим виртуальную среду в папке `bananaAPI`.

```shell
python -m venv env
```

### Далее установим зависимости.

```shell
pip install -r requirements.txt
```

## **Приступаем к основным командам:**
## Узнать текущий баланс аккаунта.
```shell
python main.py -current_balance
```

## Получить ордера по символу, возможность сохранения ордеров в excel файл. По умолчанию, ордера не сохраняются в файл.
```shell
python main.py -trades=USDTRUB -to_excel=True
```

## Сохранить цены спроса и предложений торговых пар (данные сохраняются в excel файле).
### Параметр -limit=3 количество предложений и спроса (цены при торговле)
```shell
python main.py -upload_all_couples -limit=3
```

## Запуск основного скрипта.
### Параметр -iter=1 означает количество итераций в цикле. Не может быть меньше или равно нулю (0). Ограничения на максимум не стоят.
```shell
python main.py -run -iter=1
```