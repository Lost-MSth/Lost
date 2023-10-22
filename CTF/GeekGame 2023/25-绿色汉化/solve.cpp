#include <bits/stdc++.h>
using namespace std;
typedef long long ll;
const int M = 19260817;
const int nb = 13337;

const int st = 1337;
const int ed = 7748521;

int search(ll n, ll k, vector<int> &a)
{
	// 宽搜 1 2 3 4 5
	if (k == n)
	{
		ll x = st;
		for (int i = 0; i < n; i++)
		{
			x = (x * 13337 + a[i] * 11) % M;
		}
		x = (x * 13337 + 66) % M;
		if (x == ed)
		{
			vector<int> sx(5);
			for (int i = 1; i < 5; i++)
			{
				sx[i] = 0;
			}
			for (int i = 0; i < n; i++)
			{
				sx[a[i]] += 1;
				cout << a[i] << " ";
			}
			cout << endl;
			if (sx[1] == 6 && sx[2] == 3 && sx[3] == 1 && sx[4] == 6)
			{
				exit(0);
			}
		}
		return 0;
	}
	for (int i = 1; i < 5; i++)
	{
		a[k] = i;
		search(n, k + 1, a);
	}
	return 0;
}

int main()
{
	ll n = 6 + 1 + 3 + 6;
	// cin >> n;
	vector<int> a(n);
	for (int i = 0; i < n; i++)
	{
		a[i] = 1;
	}
	search(n, 0, a);
	cout << "Angry!";
	for (int i = 0; i < n; i++)
	{
		cout << a[i] << " ";
	}
	return 0;
}