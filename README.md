Данная Ansible роль предназначена для деплоя докеризированного веб приложения на удалённый сервер.
Может использоваться как для создания Staging сборок приложений так и для деплоя приложения в production окружение.
Имеется поддержка генерации конфигурационных файлы в форматах `.env` и `.ini`.
Адрес сборки может быть:
 * уникальным для каждой сборки;
 * статичным в рамках одной ветки;
 * жёстко заданным;
 * составным (переменная и статичные части);

HTTPS:
Использовать ранее созданные сертификаты (способы дистрибьюции сертификата и ключа к нему не входит в обсуждение);
Возможность генерации Let's Encrypt сертификата.

В конфигурацию Nginx для каждого location добавляется следующая информация:

Добавочный header | Опция для отключения
---|---
Короткий хэш коммита (CI_COMMIT_SHORT_SHA) | disable_sha1_header
Уникальный номер pipeline в раках которого осуществлялась сборка (CI_PIPELINE_ID) | disable_build_id_header
Дата сборки | disable_build_date_header
X-Robots-Tag "noindex, nofollow, nosnippet, noarchive" | allow_robots_x_tag
proxy_set_header    Host            $host; | proxy_header_disabled*
proxy_set_header    X-Real-IP       $remote_addr; | proxy_header_disabled*
proxy_set_header    X-Forwarded-for $remote_addr; | proxy_header_disabled*
- `*` если выставлен параметр `proxy_path` или задан `port_name`. Опцию достаточно указать один раз для отключения трёх заголовков.

Примеры:
1) Уникальный динамическим адрес сборки:
```yaml
- hosts: destination
  become: true

  roles:
    - role: staging2
```

2) Статичный адрес сборки в рамках одной ветки:
```yaml
- hosts: destination
  become: true

  roles:
    - role: staging2
      static_staging: true
```

3) Жёстко заданный адрес сборки (доменное имя должно указывать на правильный IP-адрес):
```yaml
- hosts: destination
  become: true

  roles:
    - role: staging2
      domains:
      - name: "some.custom.domain."
        locations:
          - location: "/"
            port_name: "FRONTEND"
```

4) Уникальный динамическим адрес сборки и поддомен. Поддоменов может быть неограниченное количетсво:
```yaml
- hosts: destination
  become: true

  roles:
    - role: staging2
      domains:
      # Base domain
      - name: "~"
        locations:
          - location: "/"
            port_name: "FRONTEND"
      # Subdomain
      - name: "sub.~"
        locations:
          - location: "/"
            port_name: "SUBDOMAIN"
```

5) Статичный адрес сборки в рамках одной ветки и поддомен:
```yaml
- hosts: destination
  become: true

  roles:
    - role: staging2
      static_staging: true
      domains:
      # Base domain
      - name: "~"
        locations:
          - location: "/"
            port_name: "FRONTEND"
      # Subdomain
      - name: "sub.~"
        locations:
          - location: "/"
            port_name: "SUBDOMAIN"
```

6) Добавляем генерацию HTTPS сертификатов для базового домена и его поддомена:
```yaml
- hosts: destination
  become: true

  roles:
    - role: staging2
      static_staging: true
      tls_generate: true
      domains:
      # Base domain
      - name: "~"
        locations:
          - location: "/"
            port_name: "FRONTEND"
      # Subdomain
      - name: "sub.~"
        locations:
          - location: "/"
            port_name: "SUBDOMAIN"
```

7) Добавляем генерацию HTTPS сертификатов только для базового домена:
```yaml
- hosts: destination
  become: true

  roles:
    - role: staging2
      static_staging: true
      domains:
      # Base domain
      - name: "~"
        tls_generate: true
        locations:
          - location: "/"
            port_name: "FRONTEND"
      # Subdomain
      - name: "sub.~"
        locations:
          - location: "/"
            port_name: "SUBDOMAIN"
```

8) Генерируем HTTPS сертификат для базового домена и используем ранее созданный для поддомена:
```yaml
- hosts: destination
  become: true

  roles:
    - role: staging2
      static_staging: true
      domains:
      # Base domain
      - name: "~"
        tls_generate: true
        locations:
          - location: "/"
            port_name: "FRONTEND"
      # Subdomain
      - name: "sub.~"
        tls_enabled:
          tls_fullchain: "/full/path/to/exists/tls/fullchain/for/this/domain"
          tls_key: "/full/path/to/exists/tls/key/for/this/domain"
        locations:
          - location: "/"
            port_name: "SUBDOMAIN"
```

9) Включаем basic авторизацию для базового домена и его поддомена:
```yaml
- hosts: destination
  become: true

  roles:
    - role: staging2
      static_staging: true
      tls_generate: true
      base_auth:
        username: "111"
        password: "123"
      domains:
      # Base domain
      - name: "~"
        locations:
          - location: "/"
            port_name: "FRONTEND"
      # Subdomain
      - name: "sub.~"
        locations:
          - location: "/"
            port_name: "SUBDOMAIN"
```

10) Включаем basic авторизацию только для базового домена и его поддомена:
```yaml
- hosts: destination
  become: true

  roles:
    - role: staging2
      static_staging: true
      tls_generate: true
      domains:
      # Base domain
      - name: "~"
        base_auth:
          username: "111"
          password: "123"
        locations:
          - location: "/"
            port_name: "FRONTEND"
      # Subdomain
      - name: "sub.~"
        locations:
          - location: "/"
            port_name: "SUBDOMAIN"
```

11) Отключаем добавление информации о pipeline, убираем информацию proxy_set_header и разрешаем поисковым роботам индексировать сайт(ы):
```yaml
- hosts: destination
  become: true

  roles:
    - role: staging2
      static_staging: true
      tls_generate: true
      domains:
      # Base domain
      - name: "~"
        base_auth:
          username: "111"
          password: "123"
        locations:
          - location: "/"
            port_name: "FRONTEND"
            allow_robots_x_tag: true
            proxy_header_disabled: true
      # Subdomain
      - name: "sub.~"
        locations:
          - location: "/"
            port_name: "SUBDOMAIN"
            disable_sha1_header: true
            disable_build_id_header: true
            disable_build_date_header: true
```

12) Проксируем посторонние сайты:
```yaml
- hosts: destination
  become: true

  roles:
    - role: staging2
      static_staging: true
      tls_generate: true
      domains:
      # Base domain
      - name: "~"
        base_auth:
          username: "111"
          password: "123"
        locations:
          - location: "/"
            proxy_pass: "example.com"
            proxy_header_disabled: true
      # Subdomain
      - name: "sub.~"
        locations:
          - location: "/"
            proxy_pass: "yandex.com"
            proxy_header_disabled: false
            proxy_proto: "https"
            proxy_timeout: 600
```

13) Генерируем INI и .env файлы для приложения:
```yaml
- hosts: destination
  become: true
  
  roles:
    - role: staging2
      static_staging: true
      tls_generate: true
      variables:
        - INI_CONF_FILE: "{{ staging_application_ini_file_path }}"
        - ENV_CONF_FILE: "{{ staging_application_env_file_path }}"
    
      staging_application_env_file: ".env"
      staging_application_env:
        - SENTRY_DSN: "{{ sentry_dsn }}"
        - api_endpoint: "{{ api_endpoint }}"

      staging_application_ini_file: "conf.ini"
      staging_application_ini:
        - name: "SectionName1"
          params:
            - KEY_NAME1: "key_value1"
              KEY_NAME2: "key_value2"
        - name: "SectionName2"
          params:
            - KEY_NAME1: "key_value1"
              KEY_NAME4: "key_value4"

      domains:
      # Base domain
      - name: "~"
        locations:
          - location: "/"
            port_name: "FRONTEND"
      # Subdomain
      - name: "sub.~"
        locations:
          - location: "/"
            port_name: "SUBDOMAIN"
```

14) Получаем значения переменных из внешнего файла в зависимости от ветки и из переменной окружения:
```yaml (vars/master.yml)
api_endpoint: "http://yandex.ru"
```
```yaml (vars/dev.yml)
api_endpoint: "http://google.ru"
```
```yaml (deploy_staging.yml)
- hosts: destination
  become: true

  vars:
    ci_commit_ref_name: "{{ lookup('env', 'CI_COMMIT_REF_NAME') }}"

  pre_tasks:
    - name: import master vars
      include_vars:
        file: "vars/master.yml"
      when: ci_commit_ref_name == "master"
      tags:
        - deploy

    - name: import dev vars
      include_vars:
        file: "vars/dev.yml"
      tags:
        - deploy

  roles:
    - role: staging2
      static_staging: true
      tls_generate: true
      variables:
        - INI_CONF_FILE: "{{ staging_application_ini_file_path }}"
        - ENV_CONF_FILE: "{{ staging_application_env_file_path }}"
    
      staging_application_env_file: ".env"
      staging_application_env:
        - SENTRY_DSN: "{{ lookup('env', 'SENTRY') }}"
        - API_ENDPOINT: "{{ api_endpoint }}"

      staging_application_ini_file: "conf.ini"
      staging_application_ini:
        - name: "SectionName1"
          params:
            - KEY_NAME1: "key_value1"
              KEY_NAME2: "key_value2"
        - name: "SectionName2"
          params:
            - KEY_NAME1: "key_value1"
              KEY_NAME4: "key_value4"

      domains:
      # Base domain
      - name: "~"
        locations:
          - location: "/"
            port_name: "FRONTEND"
      # Subdomain
      - name: "sub.~"
        locations:
          - location: "/"
            port_name: "SUBDOMAIN"
```

15) Выставляем таймаут чтения ответа от прокси:
```yaml
- hosts: destination
  become: true

  roles:
    - role: staging2
      static_staging: true
      tls_generate: true
      domains:
      # Base domain
      - name: "~"
        base_auth:
          username: "111"
          password: "123"
        locations:
          - location: "/"
            proxy_pass: "example.com"
            proxy_header_disabled: true
            proxy_read_timeout: 600            
```

16) Add cron task
```yaml
- hosts: destination
  become: true

  roles:
    - role: staging2
      static_staging: true
      cron_in_docker:
        - job: "container_name_in_your_docker_compose command_to_execute_in_container"
          name: "task name" (optional)
          # Require at least one
          month: "12"
          day: "1,30"
          # 0 - Sunday; 1 - Monday ...
          weekday: ""
          hour: "19,23"
          minute: "*/5"
```
17) Public some service, available in VPN only:
deployment\deploy_staging.yml:
```yaml
- hosts: destination
  become: true

  roles:
    - role: staging2
      static_staging: true
      public_services:
        - "DB"
```
docker_compose_stage.yml:
```yaml
version: "3.7"

services:
  app:
    image: "nginxdemos/hello"
    ports:
      - "127.0.0.1:${FRONTEND}:80"
  db:
    image: "${IMAGE_PATH_DB}"
    environment:
      POSTGRES_DB: db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: 123
      PGDATA: /var/lib/postgresql/data/pgdata
    ports:
      - "${INTERNAL_IP}:${DB}:5432"
    networks:
      - default
```

18) Зарегистрировать доменное имя в DNS example.ru
```yaml
- hosts: destination
  become: true

  vars:
    project_name: "{{ lookup('env', 'CI_PROJECT_NAME') | replace('_', '-') | replace('/', '-') | lower }}"
    branch_name: "{{ lookup('env', 'CI_COMMIT_BRANCH') | replace('_', '-') | replace('/', '-') | lower }}"
    domain_name: "{{ project_name }}-{{ branch_name }}.example.ru"

  roles:
    - role: staging2
      static_staging: true
      register_domain_name: true
      domains:
        # Dot in the end of line (after domain_name) is required!
        - name: "{{ domain_name }}."
          locations:
            - location: "/"
              port_name: "NGINX"
```

19) Для сборки генерируется доменное имя третьего уровня, например - `megaproject-master.example.ru`.
```yaml
- hosts: destination
  become: true

  roles:
    - role: staging2
      static_staging: true
      register_domain_name: true
      deploy_third_domain: true
      domains:
        - name: "~"
          locations:
            - location: "/"
              port_name: "NGINX"
```

20) Зарегистрировать адрес стэйджинговой сборки (домен) в Yandex DNS (pdd.yandex.ru).
Необходимо получить API токен админиcтратора домена для добавления записей Yandex DNS 
```yaml
- hosts: destination
  become: true

  roles:
    - role: staging2
      static_staging: true
      register_domain_name: true
      deploy_third_domain: true
      yandex_pdd_oauth_token: "your yandex pdd token"
      domains:
        - name: "~"
          locations:
            - location: "/"
              port_name: "NGINX"
```

21) Опубликовать сборку Staging на другой домен второго уровня (домен должен быть делегирован нам и мы должны быть его администраторами).
```yaml
- hosts: destination
  become: true

  roles:
    - role: staging2
      static_staging: true
      register_domain_name: true
      deploy_third_domain: true
      yandex_pdd_oauth_token: "your yandex pdd token"
      base_domain_name: "another-one-domain.ru"
      domains:
        - name: "~"
          locations:
            - location: "/"
              port_name: "NGINX"
```
В данном случае сборка ветки task-911 для проекта Perpetuum-Mobile будет доступна по адресу - perpetuum-mobile-task-911.another-one-domain.ru.
Данная сборка будет доступна как внутри домена, так и из мира.

22) Скопировать некоторую папку или файл с gitlab-runner на целевой хост
```yaml
---
- hosts: destination
  become: true

  roles:
    - role: staging2
      static_staging: true
      distribute_files:
        - src: "/tmp/source_file1" # absolute path to source file
          dst: "destination_file1" # file path relative to the project root
---
- hosts: destination
  become: true

  roles:
    - role: staging2
      static_staging: true
      distribute_files:
        - src: "{{ parent_folder_path }}/source_file1" # absolute path to source file
          dst: "destination_file1" # file path relative to the project root
```

23) Увеличение таймаута работы **docker-compose up**:
```
Заходим в настройки проекта Gitlab -> CI/CD -> Variables
и задаем новую переменную CI_COMPOSE_HTTP_TIMEOUT
В поле значения, выставляем новый таймаут в секундах!
```
