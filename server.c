#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>
#include "cJSON.h"
#include <curl/curl.h>
#include <math.h>
#include <time.h>

#define BUFFER_SIZE 1024
#define MAX_SERVICES 100
#define MAX_FUNCTIONS 300
#define MAX_FNAME 30
#define MAX_PARAMS 10
#define READ_INTERVAL 60000

char names[MAX_SERVICES][MAX_FNAME];
char functions[MAX_SERVICES][MAX_FNAME];
char numservices;
char faasserver[] = "127.0.0.1";
int faasport = 8080;
int port = 8083;

// Definir la estructura para cada función
typedef struct {
    char name[50];
    char service[50];
    int execTime;
    int cost;
    int ux;
    double energy;
} Function;

Function func_db[MAX_FUNCTIONS];
int func_db_size = 0;  // Número de funciones cargadas

typedef struct {
    char name[128];
    char cid[128];
} Instance;

typedef struct {
    char name[128];
    long long time;
    char has_alt;
} FData;

FData f_data[MAX_FUNCTIONS];
int registered_functions = 0;
pthread_mutex_t f_data_mutex = PTHREAD_MUTEX_INITIALIZER;

// Función auxiliar para extraer los parámetros de la URL y almacenarlos en arrays
int parse_parameters(const char *query, char keys[][BUFFER_SIZE], char values[][BUFFER_SIZE]) {
    int param_count = 0;
    char params[BUFFER_SIZE];
    strncpy(params, query, BUFFER_SIZE);
    
    // Divide la cadena de parámetros usando '&' como delimitador
    char *param = strtok(params, "&");
    while (param != NULL && param_count < MAX_PARAMS) {
        // Divide cada parámetro en clave y valor usando '='
        sscanf(param, "%[^=]=%s", keys[param_count], values[param_count]);
        
        param_count++;
        param = strtok(NULL, "&");
    }
    
    return param_count;  // Retorna el número de parámetros extraídos
}

char loadServices(const char *filename) {
    FILE *file = fopen(filename, "r");
    if (file == NULL) {
        perror("No se pudo abrir el archivo JSON");
        return 0;
    }

    // Leer el archivo completo
    fseek(file, 0, SEEK_END);
    long length = ftell(file);
    fseek(file, 0, SEEK_SET);
    char *data = malloc(length + 1);
    fread(data, 1, length, file);
    fclose(file);
    data[length] = '\0';

    // Parsear el JSON
    cJSON *json = cJSON_Parse(data);
    if (json == NULL) {
        perror("Error al parsear JSON");
        free(data);
        return 0;
    }

    // Obtener el array "services"
    cJSON *services = cJSON_GetObjectItem(json, "services");
    if (!cJSON_IsArray(services)) {
        perror("El JSON no contiene un array 'services'");
        cJSON_Delete(json);
        free(data);
        return 0;
    }

    // Recorrer los objetos en "services"
    cJSON *service;
    char numservices = 0;
    cJSON_ArrayForEach(service, services) {
        if (numservices >= MAX_SERVICES) break;

        cJSON *name = cJSON_GetObjectItem(service, "name");
        cJSON *function = cJSON_GetObjectItem(service, "function");
        
        if (cJSON_IsString(name) && cJSON_IsString(function)) {
            strncpy(names[numservices], name->valuestring, BUFFER_SIZE - 1);
            strncpy(functions[numservices], function->valuestring, BUFFER_SIZE - 1);
            numservices++;
        }
    }

    // Limpiar memoria si no se encontró el "name"
    cJSON_Delete(json);
    free(data);
    return numservices;
}

// Función para buscar una función por servicio
char* get_function_by_name(const char *name_value, char numservices) {
    for (int i = 0; i < numservices; i++) {
        if (strcmp(names[i], name_value) == 0) {
            return functions[i];
        }
    }
    return NULL;  // Retorna NULL si no se encuentra el nombre
}

// Función para cargar la base de datos de funciones
void loadFunctions(const char *nombre_archivo) {
    // Leer el contenido del archivo
    FILE *archivo = fopen(nombre_archivo, "r");
    if (archivo == NULL) {
        printf("Error al abrir el archivo.\n");
        return;
    }

    fseek(archivo, 0, SEEK_END);
    long longitud = ftell(archivo);
    fseek(archivo, 0, SEEK_SET);

    char *contenido = (char *)malloc(longitud + 1);
    if (contenido == NULL) {
        printf("Error al asignar memoria.\n");
        fclose(archivo);
        return;
    }

    fread(contenido, 1, longitud, archivo);
    contenido[longitud] = '\0';
    fclose(archivo);

    // Analizar el JSON
    cJSON *json = cJSON_Parse(contenido);
    free(contenido); // Liberar la memoria después de parsear
    if (json == NULL) {
        printf("Error al analizar el JSON.\n");
        return;
    }

    cJSON *functions = cJSON_GetObjectItem(json, "functions");
    if (!cJSON_IsArray(functions)) {
        printf("El JSON no contiene una lista de funciones.\n");
        cJSON_Delete(json);
        return;
    }

    int num_functions = cJSON_GetArraySize(functions);

    for (int i = 0; i < num_functions && i < MAX_FUNCTIONS; i++) {
        cJSON *function = cJSON_GetArrayItem(functions, i);

        cJSON *name = cJSON_GetObjectItem(function, "name");
        cJSON *service = cJSON_GetObjectItem(function, "service");
        cJSON *execTime = cJSON_GetObjectItem(function, "execTime");
        cJSON *cost = cJSON_GetObjectItem(function, "cost");
        cJSON *ux = cJSON_GetObjectItem(function, "ux");
        cJSON *energy = cJSON_GetObjectItem(function, "energy");

        if (cJSON_IsString(name) && cJSON_IsString(service) && 
            cJSON_IsNumber(execTime) && cJSON_IsNumber(cost) &&
            cJSON_IsNumber(ux) && cJSON_IsNumber(energy)) {

            strcpy(func_db[func_db_size].name, name->valuestring);
            strcpy(func_db[func_db_size].service, service->valuestring);
            func_db[func_db_size].execTime = execTime->valueint;
            func_db[func_db_size].cost = cost->valueint;
            func_db[func_db_size].ux = ux->valueint;
            func_db[func_db_size].energy = energy->valuedouble;
            func_db_size++;
        }
    }

    cJSON_Delete(json);
}

// Función para contar el número de funciones para un mismo servicio
int numFunctions(const char *sname) {
    int count = 0;

    for (int i = 0; i < func_db_size; i++) {
        if (strcmp(func_db[i].service, sname) == 0) {
            count++;
        }
    }

    return count;
}

// Estructura para almacenar la respuesta
struct response_data {
    char *memory;
    size_t size;
};

// Callback de escritura para almacenar la respuesta en la estructura
size_t write_callback(void *ptr, size_t size, size_t nmemb, void *userdata) {
    size_t total_size = size * nmemb;
    struct response_data *data = (struct response_data *)userdata;

    // Redimensionar la memoria para añadir nuevos datos
    char *ptr_new = realloc(data->memory, data->size + total_size + 1);
    if (ptr_new == NULL) {
        printf("Error: no se pudo asignar memoria\n");
        return 0;
    }

    data->memory = ptr_new;
    memcpy(&(data->memory[data->size]), ptr, total_size);
    data->size += total_size;
    data->memory[data->size] = '\0';

    return total_size;
}

// Función para realizar la petición GET y devolver la respuesta
char* http_get(const char *url) {
    CURL *curl;
    CURLcode res;

    // Inicializar la estructura de respuesta
    struct response_data data;
    data.memory = malloc(1);  // Comenzar con un bloque de memoria vacío
    data.size = 0;

    // Inicializar libcurl
    curl = curl_easy_init();

    if (curl) {
        // Configurar la URL de la petición GET
        curl_easy_setopt(curl, CURLOPT_URL, url);

        // Configurar la función de escritura y la estructura de respuesta
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)&data);

        // Realizar la petición
        res = curl_easy_perform(curl);

        // Comprobar si hubo un error
        if (res != CURLE_OK) {
            fprintf(stderr, "Error en curl_easy_perform(): %s\n", curl_easy_strerror(res));
            free(data.memory);
            data.memory = NULL;
        }

        // Limpiar
        curl_easy_cleanup(curl);
    }

    // Retornar la respuesta (o NULL si hubo un error)
    return data.memory;
}

// Función para obtener el valor de data->result[0]->value[1]
char* get_value(const char *json_string) {
    cJSON *json = cJSON_Parse(json_string);
    if (json == NULL) {
        fprintf(stderr, "Error al parsear JSON\n");
        return NULL;
    }

    // Navegar por cada nivel de profundidad del JSON
    cJSON *data = cJSON_GetObjectItem(json, "data");
    if (data == NULL) {
        fprintf(stderr, "No se encontró el objeto 'data'\n");
        cJSON_Delete(json);
        return NULL;
    }

    cJSON *result = cJSON_GetObjectItem(data, "result");
    if (!cJSON_IsArray(result) || cJSON_GetArraySize(result) == 0) {
        fprintf(stderr, "El JSON no contiene un array 'result' válido\n");
        cJSON_Delete(json);
        char *result_value = strdup("0");
        return result_value;
    }

    // Acceder al primer elemento de "result"
    cJSON *first_result = cJSON_GetArrayItem(result, 0);
    if (first_result == NULL) {
        fprintf(stderr, "No se encontró el primer elemento de 'result'\n");
        cJSON_Delete(json);
        return NULL;
    }

    // Acceder al array "value"
    cJSON *value = cJSON_GetObjectItem(first_result, "value");
    if (!cJSON_IsArray(value) || cJSON_GetArraySize(value) <= 1) {
        fprintf(stderr, "El JSON no contiene un array 'value' con el índice 1\n");
        cJSON_Delete(json);
        return NULL;
    }

    // Obtener el elemento en value[1]
    cJSON *value_1 = cJSON_GetArrayItem(value, 1);
    if (!cJSON_IsString(value_1)) {
        fprintf(stderr, "El elemento en 'value[1]' no es una cadena\n");
        cJSON_Delete(json);
        return NULL;
    }

    // Crear una copia de value[1] y retornar
    char *result_value = strdup(value_1->valuestring);
    cJSON_Delete(json);
    return result_value;
}

long long get_ms() {
    struct timespec t;
    clock_gettime(CLOCK_REALTIME, &t);
    return (long long)(t.tv_sec * 1000) + (t.tv_nsec / 1000000);
}

FData *getFunctionData(char *fname, char *sname) {
    int i;

    pthread_mutex_lock(&f_data_mutex); // Bloqueo al iniciar la función
    for (i=0; i<registered_functions; i++) {
        if (strcmp(fname, f_data[i].name) == 0) {
            pthread_mutex_unlock(&f_data_mutex); // Desbloqueo antes de devolver
            return &f_data[i];
        }
    }
    if (i == registered_functions && registered_functions < MAX_FUNCTIONS) {
        strcpy(f_data[i].name, fname);
        f_data[i].time = 0;
        char n = numFunctions(sname);
        if (n > 1) f_data[i].has_alt = 1;
        else f_data[i].has_alt = 0;
        registered_functions++;
        pthread_mutex_unlock(&f_data_mutex); // Desbloqueo tras modificar
        return &f_data[i];
    }

    pthread_mutex_unlock(&f_data_mutex); // Desbloqueo en caso de no encontrar ni registrar
    return NULL; // Devuelve NULL si el array está lleno o no se pudo registrar
}

// Función para contar las ocurrencias de un servicio
int contarServicios(const char *json_str, const char *service_name) {
    cJSON *json = cJSON_Parse(json_str);
    if (json == NULL) {
        printf("Error al analizar el JSON.\n");
        return -1;
    }

    cJSON *functions = cJSON_GetObjectItem(json, "functions");
    if (!cJSON_IsArray(functions)) {
        printf("El JSON no contiene una lista de funciones.\n");
        cJSON_Delete(json);
        return -1;
    }

    int count = 0;
    int num_functions = cJSON_GetArraySize(functions);

    for (int i = 0; i < num_functions; i++) {
        cJSON *function = cJSON_GetArrayItem(functions, i);
        cJSON *service = cJSON_GetObjectItem(function, "service");

        if (cJSON_IsString(service) && (strcmp(service->valuestring, service_name) == 0)) {
            count++;
        }
    }

    cJSON_Delete(json);
    return count;
}

double safe_strtod(const char *text) {
    char *end;
    double num = strtod(text, &end);

    // Verificar si el texto no se pudo convertir completamente
    if (*end != '\0' && *end != '\n') {
        printf("Advertencia: parte del texto no se pudo convertir completamente.\n");
    }

    // Si el resultado es NaN, retornar 0
    if (isnan(num)) {
        return 0.0;
    }

    return num;
}

char* getInstance(const char *fname) {
    char command[256];
    snprintf(command, sizeof(command), "faas logs %s --instance --lines 1 --tail=false", fname);

    FILE *fp = popen(command, "r");
    if (fp == NULL) {
        perror("Error al ejecutar el comando");
        return NULL;
    }

    // Leer la salida del comando
    char output[1024];
    if (fgets(output, sizeof(output), fp) == NULL) {
        perror("Error al leer la salida del comando");
        pclose(fp);
        return NULL;
    }

    pclose(fp);

    // Buscar los paréntesis en la salida
    char *start = strchr(output, '(');
    char *end = strchr(output, ')');
    if (start == NULL || end == NULL || start >= end) {
        fprintf(stderr, "Error: no se encontraron paréntesis en la salida.\n");
        return NULL;
    }

    // Extraer el contenido entre los paréntesis
    size_t len = end - start - 1;
    char *instance = malloc(len + 1);
    if (instance == NULL) {
        perror("Error al asignar memoria");
        return NULL;
    }
    strncpy(instance, start + 1, len);
    instance[len] = '\0';  // Añadir el terminador nulo

    return instance;
}

Instance* getInstances(const char *fname, int *count) {
    *count = 0;
    Instance *instances = NULL;

    // Ejecuta el comando "crictl ps" y captura la salida
    FILE *fp = popen("sudo crictl ps", "r");
    if (fp == NULL) {
        perror("Error al ejecutar el comando");
        return NULL;
    }

    // Lee la salida del comando línea por línea
    char line[1024];
    while (fgets(line, sizeof(line), fp) != NULL) {
        // Verifica si la línea contiene `fname`
        if (strstr(line, fname) && strstr(line, "Running")) {
            // Encuentra el contenedor ID (cid)
            char *cid_start = line;
            char *cid_end = strchr(cid_start, ' ');
            if (cid_end == NULL) continue;

            // Encuentra el nombre de la instancia (iname)
            char *name_start = strrchr(line, ' ');
            if (name_start == NULL || name_start <= cid_end) continue;
            name_start++;

            // Incrementa el conteo y reserva memoria para la instancia
            instances = realloc(instances, (*count + 1) * sizeof(Instance));
            if (instances == NULL) {
                perror("Error al asignar memoria");
                pclose(fp);
                return NULL;
            }

            // Copia el CID y el nombre en la estructura de instancia
            snprintf(instances[*count].cid, cid_end - cid_start + 1, "%s", cid_start);
            snprintf(instances[*count].name, sizeof(instances[*count].name), "%s", name_start);

            // Incrementa el número de instancias encontradas
            (*count)++;
        }
    }

    pclose(fp);
    return instances;
}

// Función que maneja cada conexión en un hilo separado
void *handle_client(void *client_socket_ptr) {
    int client_socket = *(int *)client_socket_ptr;
    free(client_socket_ptr);  // Liberar la memoria reservada para el socket del cliente

    char buffer[BUFFER_SIZE];
    int bytes_read = read(client_socket, buffer, BUFFER_SIZE - 1);
    
    if (bytes_read < 0) {
        perror("Error reading from client");
        close(client_socket);
        return NULL;
    }
    
    buffer[bytes_read] = '\0';

    char method[8];
    char url[BUFFER_SIZE];
    char f_url[BUFFER_SIZE];
    // Arrays para almacenar claves y valores de los parámetros
    char keys[MAX_PARAMS][BUFFER_SIZE];
    char values[MAX_PARAMS][BUFFER_SIZE];
    double exectime, rate, energy, total_energy = 0, unitary_energy = 0;

    // Extraer el método y la URL
    sscanf(buffer, "%s /%s", method, url);

    // Verifica si la petición es GET
    if (strcmp(method, "GET") == 0) {
        // Buscar si hay parámetros en la URL
        char *query_start = strchr(url, '?');
        if (query_start != NULL) {
            // Extraer la cadena de parámetros
            *query_start = '\0';  // Termina la URL base
            query_start++;        // Apunta al inicio de los parámetros
            parse_parameters(query_start, keys, values);  // Analizar los parámetros
        }
        char *fname = get_function_by_name(url, numservices);
        if (fname != NULL) {
            printf("Requesting function %s\n", fname);

            sprintf(f_url, "http://%s:%d/function/%s", faasserver, faasport, fname);
            
            char *resp = http_get(f_url);

            if (resp) {
                printf(resp);
                free(resp);  // Liberar la memoria de la respuesta
            } else {
                printf("No se pudo obtener la respuesta.\n");
            }

            FData *fd = getFunctionData(fname, url);
            if (fd == NULL) {
                printf("Max functions exceeded");
                exit;
            }
            long long t = get_ms();
            if (fd->time == 0) fd->time = t;
            else if (((t - fd->time) >= READ_INTERVAL) && (fd->has_alt == 1)) {
                fd->time = t;
                sprintf(f_url, "http://%s:9090/api/v1/query?query=(rate(gateway_functions_seconds_sum{function_name='%s.openfaas-fn'}[1m])/rate(gateway_functions_seconds_count{function_name='%s.openfaas-fn'}[1m]))", faasserver, fname, fname);

                resp = http_get(f_url);
                
                if (resp) {
                    char *result = get_value(resp);
                    exectime = safe_strtod(result);
                    printf("Execution tima: %f\n", exectime);
                    free(result);
                    free(resp);  // Liberar la memoria de la respuesta
                } else {
                    printf("No se pudo obtener la respuesta.\n");
                }

                sprintf(f_url, "http://%s:9090/api/v1/query?query=increase(gateway_function_invocation_total{function_name='%s.openfaas-fn'}[1m])", faasserver, fname);

                resp = http_get(f_url);
                
                if (resp) {
                    char *result = get_value(resp);
                    rate = safe_strtod(result);
                    printf("Rate: %f\n", rate);
                    free(result);
                    free(resp);  // Liberar la memoria de la respuesta
                } else {
                    printf("No se pudo obtener la respuesta.\n");
                }

                int num_replicas;
                char *instance;
                char iname[128];
                Instance *instances = getInstances(fname, &num_replicas);
                if (instances) {
                    printf("Réplicas: %d\n", num_replicas);
                    if (num_replicas != 1) {
                        instance = getInstance(fname);
                        if (instance) {
                            printf("Instancia: %s\n", instance);
                            strcpy(iname, instance);
                            free(instance);  // Liberar la memoria
                        }
                        else {
                            strcpy(iname, instances[0].name);
                            printf("No se pudo obtener la instancia.\n");
                        }
                    }
                    // recorremos las instancias:
                    for (int i = 0; i < num_replicas; i++) {
                        sprintf(f_url, "http://%s:9090/api/v1/query?query=kepler_container_joules_double_avg{container_name=~'%s',container_id=~'%s.*'}", faasserver, fname, instances[i].cid);

                        resp = http_get(f_url);
                        
                        if (resp) {
                            char *result = get_value(resp);
                            energy = safe_strtod(result);
                            printf("Energy: %f\n", energy);
                            total_energy += energy;
                            free(result);
                            free(resp);  // Liberar la memoria de la respuesta
                        } else {
                            printf("No se pudo obtener la respuesta.\n");
                        }
                    }
                    unitary_energy = total_energy / rate;
                    printf("Unitary energy: %f\n", unitary_energy);
                    free(instances);  // Liberar la memoria asignada
                } else {
                    printf("No se encontraron instancias activas.\n");
                }
            }
            // Respuesta HTML
            const char *response =
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/html\r\n"
                "Connection: close\r\n\r\n"
                "<html><body><h1>Ok</h1></body></html>\r\n";
            write(client_socket, response, strlen(response));
        } else {
            printf("Bad request: unknown function: %s", fname);
            // Respuesta de error
            const char *error_response =
                "HTTP/1.1 400 Bad Request\r\n"
                "Content-Type: text/html\r\n"
                "Connection: close\r\n\r\n"
                "<html><body><h1>400 Bad Request</h1></body></html>\r\n";
            write(client_socket, error_response, strlen(error_response));
        }
    } else {
        // Respuesta para cualquier otra petición que no sea GET
        const char *not_found_response =
            "HTTP/1.1 404 Not Found\r\n"
            "Content-Type: text/html\r\n"
            "Connection: close\r\n\r\n"
            "<html><body><h1>404 Not Found</h1></body></html>\r\n";

        write(client_socket, not_found_response, strlen(not_found_response));
    }

    fflush(stdout);

    close(client_socket);  // Cerrar el socket del cliente
    return NULL;
}

int main() {
    // Inicializar libcurl
    curl_global_init(CURL_GLOBAL_DEFAULT);

    numservices = loadServices("configc.json");
    loadFunctions("repository-face.json");
    /*char *fname = get_function_by_name("FaceDetect", numservices);
        printf("%s", fname);
        return;*/
    int server_socket, *client_socket_ptr;
    struct sockaddr_in server_addr, client_addr;
    socklen_t addr_len = sizeof(client_addr);

    // Crear el socket
    if ((server_socket = socket(AF_INET, SOCK_STREAM, 0)) == 0) {
        perror("Error al crear el socket");
        exit(EXIT_FAILURE);
    }

    // Configuración del servidor
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(port);

    // Asignar puerto al socket
    if (bind(server_socket, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Error en bind");
        close(server_socket);
        exit(EXIT_FAILURE);
    }

    // Escuchar conexiones entrantes
    if (listen(server_socket, 5) < 0) {
        perror("Error en listen");
        close(server_socket);
        exit(EXIT_FAILURE);
    }

    printf("Function server started at port %d\n", port);

    while (1) {
        // Aceptar una conexión entrante
        client_socket_ptr = malloc(sizeof(int));
        if ((*client_socket_ptr = accept(server_socket, (struct sockaddr *)&client_addr, &addr_len)) < 0) {
            perror("Error en accept");
            free(client_socket_ptr);
            continue;
        }

        // Crear un hilo para manejar la conexión
        pthread_t thread_id;
        if (pthread_create(&thread_id, NULL, handle_client, (void *)client_socket_ptr) != 0) {
            perror("Error al crear el hilo");
            free(client_socket_ptr);
            continue;
        }

        // Separar el hilo para que se maneje automáticamente
        pthread_detach(thread_id);
    }

    // Finalizar libcurl
    curl_global_cleanup();

    close(server_socket);
    return 0;
}
