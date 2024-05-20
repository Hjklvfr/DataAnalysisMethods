import React from 'react';
import VRIA from 'vria';
import { Scene } from 'aframe-react';

const config = {
  title: 'My first VRIA app',
  data: {
    values: [
      { a: 'A', b: 1 },
      { a: 'B', b: 2 }
    ]
  },
  mark: 'bar',
  encoding: {
    x: { field: 'a', type: 'nominal' },
    y: { field: 'b', type: 'quantitative' }
  }
};

export default function VrWidget() {
  return <Scene>
    <VRIA config={config} />
  </Scene>
}