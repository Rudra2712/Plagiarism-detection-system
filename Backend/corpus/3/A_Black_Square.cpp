#include <bits/stdc++.h>
using namespace std;
int main()
{
    int a, b, c, d;
    cin >> a >> b >> c >> d;
    string s;
    cin >> s;
    int ans = 0;
    for (char ch : s)
    {
        if (ch == '1')
            ans += a;
        else if (ch == '2')
            ans += b;
        else if (ch == '3')
            ans += c;
        else if (ch == '4')
            ans += d;
    }
    cout << ans;

    return 0;
}