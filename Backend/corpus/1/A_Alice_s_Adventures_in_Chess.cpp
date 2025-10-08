#include <bits/stdc++.h>
using namespace std;
int main()
{
    int t;
    cin >> t;
    while (t--)
    {
        int n, x, y;
        int a, b;
        a = 0, b = 0;
        cin >> n >> x >> y;
        string s;
        cin >> s;
        bool k = false;
        for (int i = 0; i < 1000; i++)
        {
            for (int j = 0; j < s.length(); j++)
            {   
                if (s[j] == 'N')
                {
                    a++;
                }
                else if (s[j] == 'E')
                {
                    b++;
                }
                else if (s[j] == 'W')
                {
                    b--;
                }
                else
                {
                    a--;
                }
                if(a==y&&b==x){
                    k=true;
                    break;
                }
            }
            if(k){
                break;
            }
        }
        
        if (k)
            cout << "YES" << endl;
        else
            cout << "NO" << endl;
    }
    return 0;
}