import React from 'react';
import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper } from '@mui/material';

export default function ConversationSummary({ summary = [] }) {
  return (
    <TableContainer 
      component={Paper} 
      sx={{ 
        borderRadius: 0,
        '& .MuiTable-root': {
          borderCollapse: 'collapse'
        },
        '& .MuiTableCell-root': {
          borderBottom: '1px solid rgba(224, 224, 224, 1)'
        }
      }}
    >
      <Table>
        <TableHead>
          <TableRow>
            <TableCell colSpan={3} align="center">
              <Typography variant="h6">Summary of questions asked by user</Typography>
              {/* Optionally, show a user or session name here */}
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell>Question</TableCell>
            <TableCell>Time elapsed for response</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {summary.length === 0 ? (
            <TableRow>
              <TableCell colSpan={3} align="center">No questions yet</TableCell>
            </TableRow>
          ) : (
            summary.map((row, idx) => (
              <TableRow key={idx}>
                <TableCell>{row.name}</TableCell>
                <TableCell>{row.question}</TableCell>
                <TableCell>{row.elapsed !== null && row.elapsed !== undefined ? `${row.elapsed} seconds` : '--'}</TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </TableContainer>
  );
} 