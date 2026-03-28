#include <vector>
#include <cstdint>
#include <queue>

void calculate(uint32_t n, uint32_t m, uint32_t *edges, uint64_t *dis)
{
    struct edge
    {
        uint32_t nxt, to, w;
    };

    std::vector<edge> e(m);
    std::vector<uint32_t> head(n, -1);
    for (uint32_t i = 0; i < m; ++i)
    {
        uint32_t u = edges[i * 3];
        uint32_t v = edges[i * 3 + 1];
        uint32_t w = edges[i * 3 + 2];
        e[i] = (edge){head[u], v, w};
        head[u] = i;
    }

    struct node
    {
        uint64_t d;
        uint32_t idx;
        bool operator<(const node &tmp) const
        {
            return d > tmp.d;
        }
    };

    std::vector<uint8_t> vis(n, 0);
    std::priority_queue<node> q;
    q.push((node){0, 0});
    while (!q.empty())
    {
        uint32_t u = q.top().idx;
        q.pop();
        if (vis[u])
        {
            continue;
        }
        vis[u] = 1;
        for (uint32_t i = head[u]; i != -1; i = e[i].nxt)
        {
            uint32_t v = e[i].to;
            uint32_t w = e[i].w;
            if (dis[v] > dis[u] + w)
            {
                dis[v] = dis[u] + w;
                if (!vis[v])
                {
                    q.push((node){dis[v], v});
                }
            }
        }
    }
}