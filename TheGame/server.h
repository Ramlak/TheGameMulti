typedef vector <player>::iterator vi;
vi find(size_t hash);

void sendall(char * buf, size_t len);
size_t crc32(size_t hash, char * string, size_t len);
extern SOCKET server_socket;
extern size_t * poly;
extern char ** logins;

struct server_msg
{
	short x;
	short y;
	float alpha;
	short hp;
	short flags;
};

struct thread_params
{
	unsigned short port;
};

void run_server(thread_params * params);