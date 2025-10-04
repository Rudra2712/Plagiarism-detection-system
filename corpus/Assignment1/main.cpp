#include <bits/stdc++.h>
using namespace std;

class Solution {
public:
    int closedIsland(vector<vector<int>>& grid) {
        int n = grid.size();
        int m = grid[0].size();
        vector<vector<int>> visited(n, vector<int>(m, 0));

        // DFS function to mark group of 0s
        auto dfs = [&](int i, int j, auto&& dfs_ref) -> void {
            if (i < 0 || j < 0 || i >= n || j >= m || grid[i][j] == 1 || visited[i][j]) 
                return;
            visited[i][j] = 1;
            dfs_ref(i+1, j, dfs_ref);
            dfs_ref(i-1, j, dfs_ref);
            dfs_ref(i, j+1, dfs_ref);
            dfs_ref(i, j-1, dfs_ref);
        };

        // Step 1: mark all border 0s
        for (int i = 0; i < n; i++) {
            if (grid[i][0] == 0 && !visited[i][0]) dfs(i, 0, dfs);
            if (grid[i][m-1] == 0 && !visited[i][m-1]) dfs(i, m-1, dfs);
        }
        for (int j = 0; j < m; j++) {
            if (grid[0][j] == 0 && !visited[0][j]) dfs(0, j, dfs);
            if (grid[n-1][j] == 0 && !visited[n-1][j]) dfs(n-1, j, dfs);
        }

        // Step 2: count closed islands
        int count = 0;
        for (int i = 1; i < n-1; i++) {
            for (int j = 1; j < m-1; j++) {
                if (grid[i][j] == 0 && !visited[i][j]) {
                    dfs(i, j, dfs);
                    count++;
                }
            }
        }

        return count;
    }
};
